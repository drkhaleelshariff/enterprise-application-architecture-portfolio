"""Submit a stored invoice to the local simulated accounting receiver."""

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from accounting_receiver import accept_invoice
from accounting_receiver import DATABASE as ACCOUNTING_DATABASE
from store_invoice import DATABASE as BILLING_DATABASE

DEFAULT_ID = "BILL-ENT-001-LEASE-001-2026-11"


def submit_invoice(
    instruction_id,
    billing_database=BILLING_DATABASE,
    accounting_database=ACCOUNTING_DATABASE,
    receiver=None,
):
    billing_database = Path(billing_database).resolve()

    # Read/write mode requires an existing billing database.
    uri = billing_database.as_uri() + "?mode=rw"

    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as con:
        row = con.execute(
            """
            SELECT payload, accounting_status
            FROM invoices WHERE instruction_id = ?
            """,
            (instruction_id,),
        ).fetchone()

    if row is None:
        raise ValueError("No stored invoice for this instruction")

    original_payload, status = row
    invoice = json.loads(original_payload)
    invoice["accounting_status"] = status

    selected_receiver = accept_invoice if receiver is None else receiver
    acknowledgement = selected_receiver(invoice, accounting_database)
    
    if (
        acknowledgement.get("status") != "accepted"
        or acknowledgement.get("invoice_id") != invoice["invoice_id"]
        or acknowledgement.get("posting_id")
        != f"POST-{invoice['invoice_id']}"
        or acknowledgement.get("result") not in {"created", "existing"}
    ):
        raise ValueError("Invalid accounting acknowledgement")

    # Accounting commits independently before this billing update.
    with closing(
        sqlite3.connect(uri, uri=True, timeout=10)
    ) as con, con:
        updated = con.execute(
            """
            UPDATE invoices
            SET accounting_status = 'acknowledged'
            WHERE instruction_id = ? AND payload = ?
            """,
            (instruction_id, original_payload),
        )

        if updated.rowcount != 1:
            raise ValueError("Stored invoice changed or disappeared")

    return {
        "instruction_id": instruction_id,
        "invoice_id": invoice["invoice_id"],
        "accounting_status": "acknowledged",
        "accounting_result": acknowledgement["result"],
        "posting_id": acknowledgement["posting_id"],
    }


def main():
    if len(sys.argv) > 2:
        print(
            "Usage: python scripts/submit_to_accounting.py [instruction_id]",
            file=sys.stderr,
        )
        return 1

    instruction_id = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_ID

    try:
        result = submit_invoice(instruction_id)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())