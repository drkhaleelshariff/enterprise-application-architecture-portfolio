"""Compare billing invoices and accounting postings without changing them."""

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from accounting_receiver import DATABASE as ACCOUNTING_DATABASE
from store_invoice import DATABASE as BILLING_DATABASE


def read_rows(database, query):
    uri = Path(database).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=10)) as con:
        return con.execute(query).fetchall()


def reconcile(
    billing_database=BILLING_DATABASE,
    accounting_database=ACCOUNTING_DATABASE,
):
    billing_rows = read_rows(
        billing_database,
        "SELECT invoice_id, payload, accounting_status FROM invoices",
    )
    accounting_rows = read_rows(
        accounting_database,
        "SELECT invoice_id, posting_id, payload FROM postings",
    )

    billing = {
        invoice_id: (json.loads(payload), status)
        for invoice_id, payload, status in billing_rows
    }
    accounting = {
        invoice_id: (posting_id, json.loads(payload))
        for invoice_id, posting_id, payload in accounting_rows
    }

    issues = []
    matched = 0

    for invoice_id in sorted(billing):
        content, status = billing[invoice_id]

        if invoice_id not in accounting:
            issues.append({
                "invoice_id": invoice_id,
                "issue": "missing_accounting_posting",
                "billing_status": status,
            })
            continue

        posting_id, posted_content = accounting[invoice_id]
        valid_content = content == posted_content
        valid_posting_id = posting_id == f"POST-{invoice_id}"

        if not valid_content:
            issues.append({
                "invoice_id": invoice_id,
                "issue": "content_mismatch",
            })

        if not valid_posting_id:
            issues.append({
                "invoice_id": invoice_id,
                "issue": "posting_id_mismatch",
            })

        if status != "acknowledged":
            issues.append({
                "invoice_id": invoice_id,
                "issue": "confirmation_not_recorded",
                "billing_status": status,
            })

        if valid_content and valid_posting_id and status == "acknowledged":
            matched += 1

    for invoice_id in sorted(set(accounting) - set(billing)):
        issues.append({
            "invoice_id": invoice_id,
            "issue": "unexpected_accounting_posting",
        })

    return {
        "billing_invoice_count": len(billing),
        "accounting_posting_count": len(accounting),
        "fully_matched_count": matched,
        "issue_count": len(issues),
        "issues": issues,
    }


def main():
    try:
        report = reconcile()
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"FAIL: reconciliation could not complete: {exc}",
              file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())