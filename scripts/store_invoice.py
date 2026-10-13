"""Persist synthetic invoices and reject conflicting repeat instructions."""
from contextlib import closing
import json
import sqlite3
import sys
from pathlib import Path

from create_invoice import create_invoice
from lease_to_billing import DEFAULT_INPUT

ROOT = Path(__file__).resolve().parents[1]
DATABASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "runtime" / "billing.sqlite3"
)


def store_invoice(lease, database=DATABASE):
    invoice = create_invoice(lease)

    # Store immutable billing content separately from processing status.
    content = {
        key: value
        for key, value in invoice.items()
        if key != "accounting_status"
    }
    payload = json.dumps(content, sort_keys=True, separators=(",", ":"))

    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database, timeout=10)) as connection, connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                instruction_id TEXT PRIMARY KEY,
                invoice_id TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                accounting_status TEXT NOT NULL
                    CHECK (accounting_status IN ('pending', 'acknowledged'))
            )
        """)

        # Serialize the lookup and insert so concurrent writers cannot
        # both treat the same instruction as new.
        connection.execute("BEGIN IMMEDIATE")

        existing = connection.execute(
            """
            SELECT payload, accounting_status
            FROM invoices
            WHERE instruction_id = ?
            """,
            (invoice["instruction_id"],),
        ).fetchone()

        if existing:
            existing_payload, status = existing

            if existing_payload != payload:
                raise ValueError(
                    "Instruction ID already exists with different content"
                )

            stored = json.loads(existing_payload)
            stored["accounting_status"] = status

            return {
                "result": "existing",
                "invoice": stored,
            }

        connection.execute(
            """
            INSERT INTO invoices
                (instruction_id, invoice_id, payload, accounting_status)
            VALUES (?, ?, ?, ?)
            """,
            (
                invoice["instruction_id"],
                invoice["invoice_id"],
                payload,
                invoice["accounting_status"],
            ),
        )

        return {
            "result": "created",
            "invoice": invoice,
        }


def main():
    if len(sys.argv) > 2:
        print(
            "Usage: python scripts/store_invoice.py [input.json]",
            file=sys.stderr,
        )
        return 1

    path = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_INPUT

    try:
        with path.open(encoding="utf-8-sig") as handle:
            lease = json.load(handle)
        result = store_invoice(lease)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())