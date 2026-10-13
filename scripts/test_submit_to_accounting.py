"""Verify accounting handoff, outage and lost-confirmation recovery."""

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import submit_to_accounting as handoff
from accounting_receiver import accept_invoice
from store_invoice import store_invoice

ROOT = Path(__file__).resolve().parents[1]
LEASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)


def billing_status(database, instruction_id):
    with closing(sqlite3.connect(database)) as con:
        return con.execute(
            "SELECT accounting_status FROM invoices WHERE instruction_id = ?",
            (instruction_id,),
        ).fetchone()[0]


def posting_count(database):
    with closing(sqlite3.connect(database)) as con:
        return con.execute("SELECT COUNT(*) FROM postings").fetchone()[0]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_timeout(action):
    try:
        action()
    except TimeoutError:
        return
    raise AssertionError("Expected simulated timeout")


def main():
    with LEASE.open(encoding="utf-8-sig") as handle:
        lease = json.load(handle)

    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)

        # Normal delivery and repeated delivery.
        billing = base / "normal-billing.sqlite3"
        accounting = base / "normal-accounting.sqlite3"
        invoice = store_invoice(lease, billing)["invoice"]
        instruction_id = invoice["instruction_id"]

        result = handoff.submit_invoice(
            instruction_id, billing, accounting
        )
        require(result["accounting_result"] == "created",
                "First submission must create a posting")
        require(billing_status(billing, instruction_id) == "acknowledged",
                "Billing must record acknowledgement")
        print("PASS: successful handoff acknowledges billing")

        result = handoff.submit_invoice(
            instruction_id, billing, accounting
        )
        require(result["accounting_result"] == "existing",
                "Repeat submission must reuse the posting")
        require(posting_count(accounting) == 1,
                "Repeat submission created a duplicate")
        print("PASS: repeat submission retains one posting")

        # Failure before accounting accepts anything.
        outage_billing = base / "outage-billing.sqlite3"
        outage_accounting = base / "outage-accounting.sqlite3"
        store_invoice(lease, outage_billing)

        with patch.object(
            handoff,
            "accept_invoice",
            side_effect=TimeoutError("Simulated accounting outage"),
        ):
            expect_timeout(
                lambda: handoff.submit_invoice(
                    instruction_id, outage_billing, outage_accounting
                )
            )

        require(
            billing_status(outage_billing, instruction_id) == "pending",
            "Outage must leave billing pending",
        )
        require(not outage_accounting.exists(),
                "Outage unexpectedly reached accounting")
        print("PASS: outage leaves billing pending without a posting")

        result = handoff.submit_invoice(
            instruction_id, outage_billing, outage_accounting
        )
        require(result["accounting_result"] == "created",
                "Recovery must create the posting")
        require(posting_count(outage_accounting) == 1,
                "Unexpected posting count after recovery")
        require(
            billing_status(outage_billing, instruction_id) == "acknowledged",
            "Recovery must acknowledge billing",
        )
        print("PASS: retry after outage completes the handoff")

        # Accounting commits, but its confirmation is lost.
        lost_billing = base / "lost-billing.sqlite3"
        lost_accounting = base / "lost-accounting.sqlite3"
        store_invoice(lease, lost_billing)

        def accept_then_lose_confirmation(invoice, database):
            accept_invoice(invoice, database)
            raise TimeoutError("Simulated lost confirmation")

        with patch.object(
            handoff,
            "accept_invoice",
            side_effect=accept_then_lose_confirmation,
        ):
            expect_timeout(
                lambda: handoff.submit_invoice(
                    instruction_id, lost_billing, lost_accounting
                )
            )

        require(posting_count(lost_accounting) == 1,
                "Accounting should have committed one posting")
        require(
            billing_status(lost_billing, instruction_id) == "pending",
            "Lost confirmation must leave billing pending",
        )
        print("PASS: lost confirmation leaves a posting and pending billing")

        result = handoff.submit_invoice(
            instruction_id, lost_billing, lost_accounting
        )
        require(result["accounting_result"] == "existing",
                "Recovery must find the committed posting")
        require(posting_count(lost_accounting) == 1,
                "Recovery created a duplicate posting")
        require(
            billing_status(lost_billing, instruction_id) == "acknowledged",
            "Recovery must acknowledge billing",
        )
        print("PASS: retry recovers confirmation without duplicate posting")

    print("\nResults: 6 passed; 0 failed")


if __name__ == "__main__":
    main()