"""Validate the synthetic Meridian application landscape."""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "projects" / "01-business-application-landscape" / "data"

SCHEMAS = {
    "entities.csv": [
        "entity_id", "name", "business_focus", "business_owner"
    ],
    "capabilities.csv": [
        "capability_id", "name", "description", "business_owner"
    ],
    "processes.csv": [
        "process_id", "name", "primary_capability_id",
        "trigger", "outcome", "process_owner"
    ],
    "applications.csv": [
        "application_id", "name", "owning_entity_id", "purpose",
        "business_owner", "technical_owner", "lifecycle_status"
    ],
    "application_capabilities.csv": [
        "application_id", "capability_id"
    ],
    "process_capabilities.csv": [
        "process_id", "capability_id"
    ],
    "application_entities.csv": [
        "application_id", "entity_id"
    ],
    "integrations.csv": [
        "integration_id", "source_application_id",
        "target_application_id", "data_exchanged", "mechanism", "owner"
    ],
}

# Registers use their ID as a unique key.
# Mapping tables use the complete pair as a unique key.
KEYS = {
    filename: columns[:1] if filename in {
        "entities.csv",
        "capabilities.csv",
        "processes.csv",
        "applications.csv",
        "integrations.csv",
    } else columns
    for filename, columns in SCHEMAS.items()
}


def validate():
    errors = []
    tables = {}

    for filename, columns in SCHEMAS.items():
        path = DATA / filename
        rows = []

        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, strict=True)

                if reader.fieldnames != columns:
                    errors.append(
                        f"{filename}: expected headers {columns}; "
                        f"found {reader.fieldnames}"
                    )
                    tables[filename] = []
                    continue

                seen = set()

                for record_number, row in enumerate(reader, start=1):
                    location = f"{filename}: record {record_number}"

                    if None in row:
                        errors.append(f"{location}: extra CSV fields")

                    clean = {
                        column: (row.get(column) or "").strip()
                        for column in columns
                    }

                    for column, value in clean.items():
                        if not value:
                            errors.append(
                                f"{location}: missing {column}"
                            )

                    key = tuple(clean[column] for column in KEYS[filename])
                    if all(key):
                        if key in seen:
                            errors.append(
                                f"{location}: duplicate key {key}"
                            )
                        seen.add(key)

                    rows.append(clean)

        except (OSError, UnicodeError, csv.Error) as exc:
            errors.append(f"{filename}: cannot read CSV: {exc}")

        if not rows:
            errors.append(f"{filename}: no data records")

        tables[filename] = rows

    def values(filename, column):
        return {
            row[column]
            for row in tables[filename]
            if row[column]
        }

    entities = values("entities.csv", "entity_id")
    capabilities = values("capabilities.csv", "capability_id")
    applications = values("applications.csv", "application_id")
    processes = values("processes.csv", "process_id")

    references = [
        ("processes.csv", "primary_capability_id", capabilities),
        ("applications.csv", "owning_entity_id", entities),
        ("application_capabilities.csv", "application_id", applications),
        ("application_capabilities.csv", "capability_id", capabilities),
        ("process_capabilities.csv", "process_id", processes),
        ("process_capabilities.csv", "capability_id", capabilities),
        ("application_entities.csv", "application_id", applications),
        ("application_entities.csv", "entity_id", entities),
        ("integrations.csv", "source_application_id", applications),
        ("integrations.csv", "target_application_id", applications),
    ]

    for filename, column, allowed in references:
        for number, row in enumerate(tables[filename], start=1):
            value = row[column]
            if value and value not in allowed:
                errors.append(
                    f"{filename}: record {number}: "
                    f"unknown {column}={value}"
                )

    coverage_checks = [
        (
            "application_capabilities.csv",
            "application_id",
            applications,
            "Application has no capability mapping",
        ),
        (
            "application_capabilities.csv",
            "capability_id",
            capabilities,
            "Capability has no supporting application",
        ),
        (
            "process_capabilities.csv",
            "process_id",
            processes,
            "Process has no capability mapping",
        ),
        (
            "application_entities.csv",
            "application_id",
            applications,
            "Application has no served entity",
        ),
        (
            "application_entities.csv",
            "entity_id",
            entities,
            "Entity has no application coverage",
        ),
    ]

    for filename, column, required, message in coverage_checks:
        for missing in sorted(required - values(filename, column)):
            errors.append(f"{message}: {missing}")

    process_pairs = {
        (row["process_id"], row["capability_id"])
        for row in tables["process_capabilities.csv"]
    }

    for row in tables["processes.csv"]:
        pair = (row["process_id"], row["primary_capability_id"])
        if all(pair) and pair not in process_pairs:
            errors.append(
                f"Process {pair[0]}: primary capability "
                f"{pair[1]} is absent from its mappings"
            )

    allowed_statuses = {"active", "planned", "retiring", "retired"}
    for row in tables["applications.csv"]:
        if row["lifecycle_status"] not in allowed_statuses:
            errors.append(
                f"Application {row['application_id']}: "
                f"invalid lifecycle_status={row['lifecycle_status']}"
            )

    allowed_mechanisms = {
        "nightly_csv_import", "manual_csv_import", "rest_api"
    }
    for row in tables["integrations.csv"]:
        if row["mechanism"] not in allowed_mechanisms:
            errors.append(
                f"Integration {row['integration_id']}: "
                f"invalid mechanism={row['mechanism']}"
            )

        if (
            row["source_application_id"]
            and row["source_application_id"] == row["target_application_id"]
        ):
            errors.append(
                f"Integration {row['integration_id']}: "
                "self-integration is outside this scenario"
            )

    for filename in SCHEMAS:
        print(f"{filename}: {len(tables[filename])} records")

    if errors:
        print(f"\nFAIL: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nPASS: inventory structure and references are valid")
    return 0


if __name__ == "__main__":
    sys.exit(validate())