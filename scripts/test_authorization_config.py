"""Verify that invalid authorization registers cannot grant access."""

import json
import shutil
import tempfile
from pathlib import Path

from authorize_lease import DATA, access_lease


def edit(folder, filename, change):
    path = folder / filename
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    change(document)
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")


def missing_file(folder):
    (folder / "roles.json").unlink()


def malformed_json(folder):
    (folder / "roles.json").write_text("{", encoding="utf-8")


def duplicate_key(folder):
    (folder / "roles.json").write_text(
        '{"schema_version":"1","schema_version":"1","roles":[]}',
        encoding="utf-8",
    )


def duplicate_identity(folder):
    edit(
        folder, "identities.json",
        lambda doc: doc["identities"].append(doc["identities"][0].copy()),
    )


def unknown_role(folder):
    edit(
        folder, "identities.json",
        lambda doc: doc["identities"][0].update(role="unknown"),
    )


def unknown_entity(folder):
    edit(
        folder, "identities.json",
        lambda doc: doc["identities"][0].update(entity_ids=["ENT-999"]),
    )


def invalid_membership_type(folder):
    edit(
        folder, "identities.json",
        lambda doc: doc["identities"][0].update(entity_ids="ENT-001"),
    )


def invalid_role_action(folder):
    edit(
        folder, "roles.json",
        lambda doc: doc["roles"][0].update(allowed_actions=["lease:write"]),
    )


def invalid_record_entity(folder):
    edit(
        folder, "leases.json",
        lambda doc: doc["leases"][0].update(entity_id="ENT-999"),
    )


def run_case(name, change):
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "data"
        shutil.copytree(DATA, folder)
        change(folder)

        try:
            access_lease("USR-001", "LEASE-001", folder=folder)
        except (OSError, ValueError):
            print(f"PASS: {name}")
        else:
            raise AssertionError(
                f"{name}: invalid configuration was not rejected"
            )


def main():
    cases = [
        ("missing register rejected", missing_file),
        ("malformed JSON rejected", malformed_json),
        ("duplicate JSON key rejected", duplicate_key),
        ("duplicate identity rejected", duplicate_identity),
        ("unknown role rejected", unknown_role),
        ("unknown entity membership rejected", unknown_entity),
        ("incorrect membership type rejected", invalid_membership_type),
        ("unsupported role action rejected", invalid_role_action),
        ("unknown lease entity rejected", invalid_record_entity),
    ]

    for name, change in cases:
        run_case(name, change)

    print("\nResults: 9 passed; 0 failed")


if __name__ == "__main__":
    main()