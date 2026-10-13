"""Verify reconciliation against controlled temporary inconsistencies."""

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from accounting_receiver import accept_invoice
from reconcile_invoices import reconcile
from store_invoice import store_invoice
from submit_to_accounting import submit_invoice

ROOT = Path(__file__).resolve().parents[1]
LEASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)


def execute(database, sql, parameters=()):
    with closing(sqlite3.connect(database)) as con, con:
        con.execute(sql, parameters)


def require_issues(report, expected):
    actual = {
        (item["invoice_id"], item["issue"])
        for item in report["issues"]
    }
    if actual != expected or report["issue_count"] != len(expected):
        raise AssertionError(f"Unexpected reconciliation report: {report}")


def main():
    with LEASE.open(encoding="utf-8-sig") as handle:
        lease = json.load(handle)

    with tempfile.TemporaryDirectory() as folder:
        billing = Path(folder) / "billing.sqlite3"
        accounting = Path(folder) / "accounting.sqlite3"

        invoice = store_invoice(lease, billing)["invoice"]
        instruction_id = invoice["instruction_id"]
        invoice_id = invoice["invoice_id"]

        submit_invoice(instruction_id, billing, accounting)

        report = reconcile(billing, accounting)
        require_issues(report, set())
        if report["fully_matched_count"] != 1:
            raise AssertionError("Expected one fully matched invoice")
        print("PASS: acknowledged invoice and posting match")

        execute(
            accounting,
            "DELETE FROM postings WHERE invoice_id = ?",
            (invoice_id,),
        )
        require_issues(
            reconcile(billing, accounting),
            {(invoice_id, "missing_accounting_posting")},
        )
        print("PASS: missing accounting posting is detected")
        accept_invoice(invoice, accounting)

        execute(
            billing,
            "UPDATE invoices SET accounting_status = 'pending'",
        )
        require_issues(
            reconcile(billing, accounting),
            {(invoice_id, "confirmation_not_recorded")},
        )
        print("PASS: unrecorded confirmation is detected")
        submit_invoice(instruction_id, billing, accounting)

        changed = {
            key: value
            for key, value in invoice.items()
            if key != "accounting_status"
        }
        changed["amount"] = "2600.00"
        execute(
            accounting,
            "UPDATE postings SET payload = ? WHERE invoice_id = ?",
            (json.dumps(changed), invoice_id),
        )
        require_issues(
            reconcile(billing, accounting),
            {(invoice_id, "content_mismatch")},
        )
        print("PASS: different posting content is detected")

        original = {
            key: value
            for key, value in invoice.items()
            if key != "accounting_status"
        }
        execute(
            accounting,
            "UPDATE postings SET payload = ? WHERE invoice_id = ?",
            (json.dumps(original), invoice_id),
        )

        execute(
            accounting,
            "UPDATE postings SET posting_id = ? WHERE invoice_id = ?",
            ("POST-INVALID", invoice_id),
        )
        require_issues(
            reconcile(billing, accounting),
            {(invoice_id, "posting_id_mismatch")},
        )
        print("PASS: incorrect posting identifier is detected")
        execute(
            accounting,
            "UPDATE postings SET posting_id = ? WHERE invoice_id = ?",
            (f"POST-{invoice_id}", invoice_id),
        )

        extra_lease = {**lease, "lease_id": "LEASE-002"}
        extra_invoice = store_invoice(
            extra_lease, Path(folder) / "other-billing.sqlite3"
        )["invoice"]
        accept_invoice(extra_invoice, accounting)

        require_issues(
            reconcile(billing, accounting),
            {
                (
                    extra_invoice["invoice_id"],
                    "unexpected_accounting_posting",
                )
            },
        )
        print("PASS: posting without a billing invoice is detected")

    print("\nResults: 6 passed; 0 failed")


if __name__ == "__main__":
    main()