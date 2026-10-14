"""Persist synthetic lease change requests after authorization."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from authorize_lease import DATA, load_data

DATABASE = DATA.parent / "runtime" / "approvals.sqlite3"


def permitted_human(identity_id, entity_id, action, identities, roles):
    identity = identities.get(identity_id)
    return (
        identity is not None
        and identity["status"] == "active"
        and identity["identity_type"] == "human"
        and entity_id in identity["entity_ids"]
        and action in roles[identity["role"]]["allowed_actions"]
    )


def initialize(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS change_requests (
            request_id TEXT PRIMARY KEY,
            lease_id TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            requester_id TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('pending', 'approved')),
            approver_id TEXT,
            CHECK (
                (status = 'pending' AND approver_id IS NULL)
                OR
                (status = 'approved'
                 AND approver_id IS NOT NULL
                 AND approver_id <> requester_id)
            )
        )
    """)


def create_request(
    requester_id, lease_id, description, folder=DATA, database=DATABASE
):
    identities, roles, leases = load_data(folder)
    lease = leases.get(lease_id)

    if lease is None or not permitted_human(
        requester_id,
        lease["entity_id"],
        "lease_change:request",
        identities,
        roles,
    ):
        raise PermissionError("Request denied")

    if (
        not isinstance(description, str)
        or not description.strip()
        or len(description) > 500
    ):
        raise ValueError("Description must contain 1 to 500 characters")

    request = {
        "request_id": f"REQ-{uuid4().hex}",
        "lease_id": lease_id,
        "entity_id": lease["entity_id"],
        "requester_id": requester_id,
        "description": description.strip(),
        "status": "pending",
        "approver_id": None,
    }

    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database, timeout=10)) as con, con:
        initialize(con)
        con.execute(
            """
            INSERT INTO change_requests
                (request_id, lease_id, entity_id, requester_id,
                 description, status, approver_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(request.values()),
        )

    return request


def main():
    parser = argparse.ArgumentParser(
        description="Create a synthetic lease change request"
    )
    parser.add_argument("requester_id")
    parser.add_argument("lease_id")
    parser.add_argument("description")
    args = parser.parse_args()

    try:
        result = create_request(
            args.requester_id, args.lease_id, args.description
        )
    except PermissionError:
        print(json.dumps({"decision": "deny"}))
        return 1
    except (OSError, ValueError, sqlite3.Error):
        print(json.dumps({
            "decision": "deny",
            "error": "invalid_input_or_unavailable_configuration",
        }))
        return 2

    print(json.dumps(result, indent=2))
    return 0

def approve_request(
    approver_id, request_id, folder=DATA, database=DATABASE
):
    identities, roles, leases = load_data(folder)
    uri = Path(database).resolve().as_uri() + "?mode=rw"

    with closing(
        sqlite3.connect(uri, uri=True, timeout=10)
    ) as con, con:
        con.row_factory = sqlite3.Row
        con.execute("BEGIN IMMEDIATE")

        row = con.execute(
            "SELECT * FROM change_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()

        if row is None:
            raise PermissionError("Approval denied")

        request = dict(row)
        lease = leases.get(request["lease_id"])

        if (
            request["status"] != "pending"
            or approver_id == request["requester_id"]
            or lease is None
            or lease["entity_id"] != request["entity_id"]
            or not permitted_human(
                approver_id,
                request["entity_id"],
                "lease_change:approve",
                identities,
                roles,
            )
        ):
            raise PermissionError("Approval denied")

        updated = con.execute(
            """
            UPDATE change_requests
            SET status = 'approved', approver_id = ?
            WHERE request_id = ? AND status = 'pending'
            """,
            (approver_id, request_id),
        )

        if updated.rowcount != 1:
            raise PermissionError("Approval denied")

        request["status"] = "approved"
        request["approver_id"] = approver_id

    return request

if __name__ == "__main__":
    raise SystemExit(main())