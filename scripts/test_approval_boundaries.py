"""Verify approval boundaries independently of role permission."""

import json
import shutil
import tempfile
from pathlib import Path

from authorize_lease import DATA
from lease_change_workflow import approve_request, create_request
from test_lease_change_workflow import denied_without_change


def main():
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "data"
        shutil.copytree(DATA, folder)
        database = Path(temporary) / "approvals.sqlite3"

        request = create_request(
            "USR-005", "LEASE-001", "Synthetic boundary test",
            folder=folder, database=database,
        )
        request_id = request["request_id"]

        path = folder / "identities.json"
        original = json.loads(path.read_text(encoding="utf-8-sig"))

        cases = [
            (
                "disabled approver denied",
                "USR-006",
                {"status": "disabled"},
            ),
            (
                "service identity denied despite approval permission",
                "SVC-001",
                {"role": "lease_change_approver"},
            ),
            (
                "cross-entity approver denied",
                "USR-006",
                {"entity_ids": ["ENT-002"]},
            ),
        ]

        for name, identity_id, changes in cases:
            document = json.loads(json.dumps(original))
            for identity in document["identities"]:
                if identity["identity_id"] == identity_id:
                    identity.update(changes)

            path.write_text(
                json.dumps(document, indent=2) + "\n", encoding="utf-8"
            )

            denied_without_change(
                database,
                lambda: approve_request(
                    identity_id, request_id,
                    folder=folder, database=database,
                ),
            )
            print(f"PASS: {name}; request unchanged")

        path.write_text(
            json.dumps(original, indent=2) + "\n", encoding="utf-8"
        )

        denied_without_change(
            database,
            lambda: approve_request(
                "USR-999", request_id,
                folder=folder, database=database,
            ),
        )
        print("PASS: unknown approver denied; request unchanged")

        approved = approve_request(
            "USR-006", request_id, folder=folder, database=database
        )
        if (
            approved["status"] != "approved"
            or approved["approver_id"] != "USR-006"
        ):
            raise AssertionError("Valid independent approval failed")
        print("PASS: valid approver succeeds after denied attempts")

    print("\nResults: 5 passed; 0 failed")


if __name__ == "__main__":
    main()