"""Verify repeat-safe acceptance by the simulated accounting receiver."""

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from accounting_receiver import accept_invoice
from create_invoice import create_invoice

ROOT = Path(__file__).resolve().parents[1]
LEASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)


def main():
    with LEASE.open(encoding="utf-8-sig") as handle:
        invoice = create_invoice(json.load(handle))

    with tempfile.TemporaryDirectory() as folder:
        database = Path(folder) / "accounting.sqlite3"

        first = accept_invoice(invoice, database)
        expected = {
            "result": "created",
            "posting_id": "POST-INV-ENT-001-LEASE-001-2026-11",
            "invoice_id": invoice["invoice_id"],
            "status": "accepted",
        }
        if first != expected:
            raise AssertionError(f"Unexpected acknowledgement: {first}")
        print("PASS: first delivery creates an accepted posting")

        repeated = accept_invoice(invoice, database)
        if repeated != {**expected, "result": "existing"}:
            raise AssertionError(f"Unexpected repeat response: {repeated}")
        print("PASS: repeat delivery returns the existing posting")

        conflicting = {**invoice, "amount": "2600.00"}
        try:
            accept_invoice(conflicting, database)
        except ValueError as exc:
            if str(exc) != "Invoice ID already posted with different content":
                raise AssertionError(f"Unexpected rejection: {exc}") from exc
        else:
            raise AssertionError("Conflicting invoice was accepted")
        print("PASS: conflicting invoice content is rejected")

        acknowledged = {**invoice, "accounting_status": "acknowledged"}
        response = accept_invoice(acknowledged, database)
        if response != repeated:
            raise AssertionError("Processing status changed posting identity")
        print("PASS: status change does not create a new posting")

        with closing(sqlite3.connect(database)) as connection:
            rows = connection.execute(
                "SELECT posting_id, payload FROM postings"
            ).fetchall()

        if len(rows) != 1:
            raise AssertionError(f"Expected one posting; found {len(rows)}")

        stored = json.loads(rows[0][1])
        if stored["amount"] != "2500.00":
            raise AssertionError("Original posting amount changed")
        print("PASS: one unchanged accounting posting remains")

    print("\nResults: 5 passed; 0 failed")


if __name__ == "__main__":
    main()