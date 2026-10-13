"""Verify HTTP handoff and failure handling with temporary databases."""

import json
import socket
import sqlite3
import tempfile
import threading
from contextlib import closing
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import accounting_http_server as api
import submit_to_accounting_http as client
from accounting_receiver import accept_invoice
from store_invoice import store_invoice
from submit_to_accounting import submit_invoice

ROOT = Path(__file__).resolve().parents[1]
LEASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)


def status(database, instruction_id):
    with closing(sqlite3.connect(database)) as con:
        return con.execute(
            "SELECT accounting_status FROM invoices WHERE instruction_id = ?",
            (instruction_id,),
        ).fetchone()[0]


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

        # Bind a socket without listening: connection attempts are refused.
        with closing(socket.socket()) as unavailable:
            unavailable.bind(("127.0.0.1", 0))
            port = unavailable.getsockname()[1]

            with patch.object(client, "PORT", port):
                try:
                    submit_invoice(
                        instruction_id,
                        billing,
                        accounting,
                        receiver=client.accept_invoice_http,
                    )
                except ConnectionRefusedError:
                    pass
                else:
                    raise AssertionError("Expected connection refusal")

        require(status(billing, instruction_id) == "pending",
                "Failed HTTP request falsely acknowledged billing")
        require(not accounting.exists(),
                "Failed request unexpectedly created accounting storage")
        print("PASS: refused connection leaves fresh invoice pending")

        def isolated_receiver(value):
            return accept_invoice(value, accounting)

        with patch.object(api, "accept_invoice", isolated_receiver):
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), api.AccountingHandler
            )
            thread = threading.Thread(target=server.serve_forever)
            thread.start()

            try:
                with patch.object(client, "PORT", server.server_address[1]):
                    first = submit_invoice(
                        instruction_id,
                        billing,
                        accounting,
                        receiver=client.accept_invoice_http,
                    )
                    require(first["accounting_result"] == "created",
                            "Recovery did not create the posting")
                    require(status(billing, instruction_id) == "acknowledged",
                            "Recovery did not acknowledge billing")
                    print("PASS: HTTP recovery posts and acknowledges invoice")

                    repeated = submit_invoice(
                        instruction_id,
                        billing,
                        accounting,
                        receiver=client.accept_invoice_http,
                    )
                    require(repeated["accounting_result"] == "existing",
                            "Repeat request did not reuse the posting")
                    print("PASS: repeated HTTP handoff reuses posting")

                    changed = {**invoice, "amount": "2600.00"}
                    try:
                        client.accept_invoice_http(changed)
                    except ValueError as exc:
                        require("HTTP 409" in str(exc),
                                f"Unexpected rejection: {exc}")
                    else:
                        raise AssertionError("HTTP conflict was accepted")
                    print("PASS: HTTP client reports content conflict")

                with closing(sqlite3.connect(accounting)) as con:
                    rows = con.execute(
                        "SELECT payload FROM postings"
                    ).fetchall()

                require(
                    len(rows) == 1
                    and json.loads(rows[0][0])["amount"] == "2500.00",
                    "Posting was changed or duplicated",
                )
                print("PASS: one unchanged posting remains")

            finally:
                server.shutdown()
                thread.join()
                server.server_close()

    print("\nResults: 5 passed; 0 failed")


if __name__ == "__main__":
    main()