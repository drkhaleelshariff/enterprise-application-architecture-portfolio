"""Exercise the accounting HTTP interface with isolated test storage."""

import json
import sqlite3
import tempfile
import threading
from contextlib import closing
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import accounting_http_server as api
from accounting_receiver import accept_invoice
from create_invoice import create_invoice

ROOT = Path(__file__).resolve().parents[1]
LEASE = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)


def request(port, method, path, body=None, headers=None):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    with LEASE.open(encoding="utf-8-sig") as handle:
        invoice = create_invoice(json.load(handle))

    with tempfile.TemporaryDirectory() as folder:
        database = Path(folder) / "accounting.sqlite3"

        def isolated_receiver(value):
            return accept_invoice(value, database)

        with patch.object(api, "accept_invoice", isolated_receiver):
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), api.AccountingHandler
            )
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            port = server.server_address[1]

            try:
                status, body = request(port, "GET", "/health")
                require(status == 200 and body == {"status": "ok"},
                        "Health response failed")
                print("PASS: health endpoint responds")

                headers = {"Content-Type": "application/json"}
                payload = json.dumps(invoice).encode("utf-8")

                status, first = request(
                    port, "POST", "/v1/postings", payload, headers
                )
                require(
                    status == 201
                    and first["result"] == "created"
                    and first["invoice_id"] == invoice["invoice_id"]
                    and first["status"] == "accepted",
                    "First posting response failed",
                )
                print("PASS: first submission returns HTTP 201")

                status, repeated = request(
                    port, "POST", "/v1/postings", payload, headers
                )
                require(
                    status == 200
                    and repeated == {**first, "result": "existing"},
                    "Repeat posting response failed",
                )
                print("PASS: repeat submission returns HTTP 200")

                conflict = json.dumps(
                    {**invoice, "amount": "2600.00"}
                ).encode("utf-8")
                status, body = request(
                    port, "POST", "/v1/postings", conflict, headers
                )
                require(status == 409 and body["error"] == "invoice_conflict",
                        "Conflict was not rejected")
                print("PASS: conflicting content returns HTTP 409")

                status, body = request(
                    port, "POST", "/v1/postings", b"{", headers
                )
                require(status == 400, "Malformed JSON was not rejected")
                print("PASS: malformed JSON returns HTTP 400")

                status, body = request(
                    port, "POST", "/v1/postings",
                    b'{"amount":"1.00","amount":"2.00"}', headers
                )
                require(status == 400, "Duplicate JSON keys were accepted")
                print("PASS: duplicate JSON keys return HTTP 400")

                status, body = request(
                    port, "POST", "/v1/postings", b"{}", headers
                )
                require(status == 422, "Invalid invoice was not rejected")
                print("PASS: invalid invoice returns HTTP 422")

                status, body = request(
                    port, "POST", "/v1/postings", payload,
                    {"Content-Type": "text/plain"},
                )
                require(status == 415, "Wrong media type was accepted")
                print("PASS: unsupported media type returns HTTP 415")

                status, body = request(port, "GET", "/v1/postings")
                require(status == 405, "GET posting request was accepted")
                print("PASS: incorrect method returns HTTP 405")

                status, body = request(port, "GET", "/unknown")
                require(status == 404, "Unknown path was accepted")
                print("PASS: unknown path returns HTTP 404")

                with closing(sqlite3.connect(database)) as con:
                    rows = con.execute(
                        "SELECT payload FROM postings"
                    ).fetchall()

                require(
                    len(rows) == 1
                    and json.loads(rows[0][0])["amount"] == "2500.00",
                    "HTTP requests changed or duplicated the posting",
                )
                print("PASS: one unchanged posting remains")

            finally:
                server.shutdown()
                thread.join()
                server.server_close()

    print("\nResults: 11 passed; 0 failed")


if __name__ == "__main__":
    main()