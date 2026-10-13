"""Verify recovery when accounting commits but HTTP confirmation is lost."""

import json
import sqlite3
import tempfile
import threading
from contextlib import closing
from http.client import RemoteDisconnected
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import accounting_http_server as api
import submit_to_accounting_http as client
from accounting_receiver import accept_invoice
from reconcile_invoices import reconcile
from store_invoice import store_invoice
from submit_to_accounting import submit_invoice

ROOT = Path(__file__).resolve().parents[1]
LEASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    with LEASE.open(encoding="utf-8-sig") as handle:
        lease = json.load(handle)

    with tempfile.TemporaryDirectory() as folder:
        billing = Path(folder) / "billing.sqlite3"
        accounting = Path(folder) / "accounting.sqlite3"
        invoice = store_invoice(lease, billing)["invoice"]
        instruction_id = invoice["instruction_id"]

        class DropFirstConfirmation(api.AccountingHandler):
            def send_json(self, status, body):
                # The receiver has committed before requesting this response.
                if status == 201 and body.get("status") == "accepted":
                    self.close_connection = True
                    return
                super().send_json(status, body)

        def isolated_receiver(value):
            return accept_invoice(value, accounting)

        with patch.object(api, "accept_invoice", isolated_receiver):
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), DropFirstConfirmation
            )
            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            try:
                with patch.object(client, "PORT", server.server_address[1]):
                    try:
                        submit_invoice(
                            instruction_id,
                            billing,
                            accounting,
                            receiver=client.accept_invoice_http,
                        )
                    except RemoteDisconnected:
                        pass
                    else:
                        raise AssertionError(
                            "Expected connection closure before confirmation"
                        )
                    print("PASS: client detects lost HTTP confirmation")

                    report = reconcile(billing, accounting)
                    require(
                        report["accounting_posting_count"] == 1
                        and report["fully_matched_count"] == 0
                        and report["issue_count"] == 1
                        and report["issues"] == [{
                            "invoice_id": invoice["invoice_id"],
                            "issue": "confirmation_not_recorded",
                            "billing_status": "pending",
                        }],
                        f"Unexpected interrupted state: {report}",
                    )
                    print("PASS: posting exists while billing remains pending")

                    recovered = submit_invoice(
                        instruction_id,
                        billing,
                        accounting,
                        receiver=client.accept_invoice_http,
                    )
                    require(
                        recovered["accounting_result"] == "existing"
                        and recovered["accounting_status"] == "acknowledged",
                        "Retry did not recover existing posting confirmation",
                    )
                    print("PASS: HTTP retry acknowledges the existing posting")

                    report = reconcile(billing, accounting)
                    require(
                        report["billing_invoice_count"] == 1
                        and report["accounting_posting_count"] == 1
                        and report["fully_matched_count"] == 1
                        and report["issue_count"] == 0,
                        f"Recovery did not reconcile: {report}",
                    )

                    with closing(sqlite3.connect(accounting)) as con:
                        payload = con.execute(
                            "SELECT payload FROM postings"
                        ).fetchone()[0]
                    require(
                        json.loads(payload)["amount"] == "2500.00",
                        "Recovery changed the posting amount",
                    )
                    print("PASS: recovery reconciles one unchanged posting")

            finally:
                server.shutdown()
                thread.join()
                server.server_close()

    print("\nResults: 4 passed; 0 failed")


if __name__ == "__main__":
    main()