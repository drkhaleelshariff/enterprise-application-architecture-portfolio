"""Verify invoice persistence, repeat delivery and conflict rejection."""

from contextlib import closing
import json
import sqlite3
import tempfile
from pathlib import Path

from store_invoice import store_invoice

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "projects" / "03-lease-to-billing" / "data"


def load(filename):
    with (DATA / filename).open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def main():
    lease = load("lease_001.json")
    conflicting = load("lease_001_conflicting.json")
    unapproved = load("lease_001_unapproved.json")

    with tempfile.TemporaryDirectory() as folder:
        database = Path(folder) / "billing.sqlite3"

        first = store_invoice(lease, database)
        if first["result"] != "created":
            raise AssertionError("First delivery must create an invoice")
        if first["invoice"]["amount"] != "2500.00":
            raise AssertionError("Unexpected invoice amount")
        print("PASS: first delivery creates the expected invoice")

        repeated = store_invoice(lease, database)
        if repeated["result"] != "existing":
            raise AssertionError("Repeat delivery must return existing")
        if repeated["invoice"] != first["invoice"]:
            raise AssertionError("Repeat delivery changed the invoice")
        print("PASS: repeat delivery returns the stored invoice")

        try:
            store_invoice(conflicting, database)
        except ValueError as exc:
            if str(exc) != (
                "Instruction ID already exists with different content"
            ):
                raise AssertionError(f"Unexpected rejection: {exc}") from exc
        else:
            raise AssertionError("Conflicting content was accepted")
        print("PASS: conflicting content is rejected")

        try:
            store_invoice(unapproved, database)
        except ValueError as exc:
            if str(exc) != (
                "Lease is not approved; no instruction generated"
            ):
                raise AssertionError(f"Unexpected rejection: {exc}") from exc
        else:
            raise AssertionError("Unapproved lease was accepted")
        print("PASS: unapproved lease is rejected")

        with closing(sqlite3.connect(database)) as connection:
            rows = connection.execute(
                "SELECT payload, accounting_status FROM invoices"
            ).fetchall()

        if len(rows) != 1:
            raise AssertionError(f"Expected one row; found {len(rows)}")

        stored = json.loads(rows[0][0])
        if stored["amount"] != "2500.00" or rows[0][1] != "pending":
            raise AssertionError("Stored invoice was unexpectedly changed")
        print("PASS: database retains one unchanged pending invoice")

    print("\nResults: 5 passed; 0 failed")


if __name__ == "__main__":
    main()