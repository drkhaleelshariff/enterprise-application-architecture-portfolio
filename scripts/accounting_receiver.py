"""Persist synthetic accounting postings with repeat-safe acceptance."""

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "runtime" / "accounting.sqlite3"
)

FIELDS = {
    "schema_version",
    "invoice_id",
    "instruction_id",
    "entity_id",
    "lease_id",
    "billing_period",
    "currency",
    "amount",
    "accounting_status",
}


def accept_invoice(invoice, database=DATABASE):
    if not isinstance(invoice, dict) or set(invoice) != FIELDS:
        raise ValueError("Unexpected invoice fields")

    for field in FIELDS:
        value = invoice[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field}: must be a nonempty string")
        if value != value.strip():
            raise ValueError(f"{field}: surrounding whitespace is not allowed")

    if invoice["schema_version"] != "1":
        raise ValueError("Unsupported invoice schema")

    if invoice["entity_id"] not in {"ENT-001", "ENT-002"}:
        raise ValueError("Unknown entity")

    if not re.fullmatch(r"LEASE-[0-9]{3}", invoice["lease_id"]):
        raise ValueError("Invalid lease identifier")

    period = invoice["billing_period"]
    if (
        not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", period)
        or period.startswith("0000-")
    ):
        raise ValueError("Invalid billing period")

    suffix = (
        f"{invoice['entity_id']}-"
        f"{invoice['lease_id']}-{period}"
    )
    if invoice["invoice_id"] != f"INV-{suffix}":
        raise ValueError("Invoice identifier does not match its content")

    if invoice["instruction_id"] != f"BILL-{suffix}":
        raise ValueError("Instruction identifier does not match its content")

    if invoice["currency"] != "EUR":
        raise ValueError("Only EUR is supported")

    if not re.fullmatch(r"[0-9]+\.[0-9]{2}", invoice["amount"]):
        raise ValueError("Invalid invoice amount")

    if invoice["accounting_status"] not in {"pending", "acknowledged"}:
        raise ValueError("Invalid accounting status")

    # Processing status is not part of immutable posting content.
    content = {
        key: value
        for key, value in invoice.items()
        if key != "accounting_status"
    }
    payload = json.dumps(content, sort_keys=True, separators=(",", ":"))
    posting_id = f"POST-{invoice['invoice_id']}"

    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database, timeout=10)) as con, con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS postings (
                invoice_id TEXT PRIMARY KEY,
                posting_id TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL
            )
        """)
        con.execute("BEGIN IMMEDIATE")

        existing = con.execute(
            "SELECT posting_id, payload FROM postings WHERE invoice_id = ?",
            (invoice["invoice_id"],),
        ).fetchone()

        if existing:
            if existing[1] != payload:
                raise ValueError(
                    "Invoice ID already posted with different content"
                )
            result = "existing"
            posting_id = existing[0]
        else:
            con.execute(
                """
                INSERT INTO postings (invoice_id, posting_id, payload)
                VALUES (?, ?, ?)
                """,
                (invoice["invoice_id"], posting_id, payload),
            )
            result = "created"

    # Return acknowledgement only after the transaction commits.
    return {
        "result": result,
        "posting_id": posting_id,
        "invoice_id": invoice["invoice_id"],
        "status": "accepted",
    }