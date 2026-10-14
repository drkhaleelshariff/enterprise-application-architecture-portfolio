"""Verify independent approval and unchanged state after denied attempts."""

import json
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from authorize_lease import DATA
from lease_change_workflow import approve_request, create_request


def snapshot(database):
    with closing(sqlite3.connect(database)) as con:
        return con.execute(
            "SELECT * FROM change_requests ORDER BY request_id"
        ).fetchall()


def denied_without_change(database, action):
    before = snapshot(database)
    try:
        action()
    except PermissionError:
        pass
    else:
        raise AssertionError("Expected permission denial")

    if snapshot(database) != before:
        raise AssertionError("Denied action changed stored requests")


def main():
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "data"
        shutil.copytree(DATA, folder)
        database = Path(temporary) / "approvals.sqlite3"

        request = create_request(
            "USR-005", "LEASE-001", "Synthetic change proposal",
            folder=folder, database=database,
        )
        request_id = request["request_id"]

        if (
            request["status"] != "pending"
            or request["requester_id"] != "USR-005"
            or request["entity_id"] != "ENT-001"
        ):
            raise AssertionError("Incorrect initial request")
        print("PASS: authorized requester creates a pending request")

        denied_without_change(
            database,
            lambda: create_request(
                "USR-001", "LEASE-001", "Unauthorized proposal",
                folder=folder, database=database,
            ),
        )
        print("PASS: reader cannot create a request")

        denied_without_change(
            database,
            lambda: create_request(
                "USR-005", "LEASE-002", "Cross-entity proposal",
                folder=folder, database=database,
            ),
        )
        print("PASS: requester cannot target another entity")

        # Give the requester both permissions in the temporary role register.
        roles_path = folder / "roles.json"
        roles = json.loads(roles_path.read_text(encoding="utf-8-sig"))
        for role in roles["roles"]:
            if role["role_id"] == "lease_change_requester":
                role["allowed_actions"].append("lease_change:approve")
        roles_path.write_text(json.dumps(roles), encoding="utf-8")

        denied_without_change(
            database,
            lambda: approve_request(
                "USR-005", request_id, folder=folder, database=database
            ),
        )
        print("PASS: self-approval denied despite both permissions")

        denied_without_change(
            database,
            lambda: approve_request(
                "USR-001", request_id, folder=folder, database=database
            ),
        )
        print("PASS: reader cannot approve")

        approved = approve_request(
            "USR-006", request_id, folder=folder, database=database
        )
        if (
            approved["status"] != "approved"
            or approved["approver_id"] != "USR-006"
        ):
            raise AssertionError("Independent approval failed")
        print("PASS: separate authorized approver approves")

        denied_without_change(
            database,
            lambda: approve_request(
                "USR-006", request_id, folder=folder, database=database
            ),
        )
        print("PASS: already approved request cannot be approved again")

        denied_without_change(
            database,
            lambda: approve_request(
                "USR-006", "REQ-UNKNOWN",
                folder=folder, database=database,
            ),
        )
        print("PASS: unknown request cannot be approved")

    print("\nResults: 8 passed; 0 failed")


if __name__ == "__main__":
    main()