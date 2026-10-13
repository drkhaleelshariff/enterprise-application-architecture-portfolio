"""Exercise the validator against temporary inventory copies."""

import csv
import io
import shutil
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import validate_inventory as validator


def edit_csv(folder, filename, change):
    path = folder / filename

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)

    change(rows)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def missing_owner(folder):
    edit_csv(
        folder,
        "applications.csv",
        lambda rows: rows[0].update(technical_owner=""),
    )


def unknown_application(folder):
    edit_csv(
        folder,
        "integrations.csv",
        lambda rows: rows[0].update(target_application_id="APP-999"),
    )


def unsupported_capability(folder):
    edit_csv(
        folder,
        "application_capabilities.csv",
        lambda rows: rows.__setitem__(
            slice(None),
            [row for row in rows if row["capability_id"] != "CAP-004"],
        ),
    )


def duplicate_mapping(folder):
    edit_csv(
        folder,
        "application_entities.csv",
        lambda rows: rows.append(rows[0].copy()),
    )


def run_case(name, change, expected_code, expected_message):
    original_data = validator.DATA

    try:
        with tempfile.TemporaryDirectory() as temporary:
            copied_data = Path(temporary) / "data"
            shutil.copytree(original_data, copied_data)

            if change:
                change(copied_data)

            validator.DATA = copied_data
            output = io.StringIO()

            with redirect_stdout(output):
                result = validator.validate()

            text = output.getvalue()

            if result != expected_code or expected_message not in text:
                raise AssertionError(
                    f"{name}: unexpected result={result}\n{text}"
                )

            print(f"PASS: {name}")

    finally:
        validator.DATA = original_data


def main():
    cases = [
        (
            "valid baseline",
            None,
            0,
            "PASS: inventory structure and references are valid",
        ),
        (
            "missing technical owner detected",
            missing_owner,
            1,
            "missing technical_owner",
        ),
        (
            "unknown integration target detected",
            unknown_application,
            1,
            "unknown target_application_id=APP-999",
        ),
        (
            "unsupported capability detected",
            unsupported_capability,
            1,
            "Capability has no supporting application: CAP-004",
        ),
        (
            "duplicate entity mapping detected",
            duplicate_mapping,
            1,
            "duplicate key",
        ),
    ]

    for case in cases:
        run_case(*case)

    print("\nPASS: all 5 validation scenarios behaved as expected")


if __name__ == "__main__":
    main()