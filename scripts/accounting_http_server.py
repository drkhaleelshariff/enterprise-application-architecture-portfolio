"""Local accounting HTTP demonstration: health endpoint only."""
import re
import sqlite3

from accounting_receiver import accept_invoice
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result

class AccountingHandler(BaseHTTPRequestHandler):
    def send_json(self, status, body):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
        elif self.path == "/v1/postings":
            self.send_json(
                405,
                {
                    "error": "method_not_allowed",
                    "message": "Use POST for this endpoint",
                },
            )
        else:
            self.send_json(
                404,
                {
                    "error": "not_found",
                    "message": "Unknown path",
                },
            )

    def do_POST(self):
        if self.path != "/v1/postings":
            status = 405 if self.path == "/health" else 404
            self.send_json(
                status,
                {
                    "error": "unsupported_request",
                    "message": "Method or path is not supported",
                },
            )
            return

        self.connection.settimeout(5)

        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get("Transfer-Encoding") is not None:
            self.send_json(
                400,
                {"error": "invalid_framing",
                 "message": "Transfer-Encoding is unsupported"},
            )
            return

        if not lengths:
            self.send_json(
                411,
                {"error": "length_required",
                 "message": "Content-Length is required"},
            )
            return

        if len(lengths) != 1 or not re.fullmatch(r"[0-9]+", lengths[0]):
            self.send_json(
                400,
                {"error": "invalid_length",
                 "message": "Invalid Content-Length"},
            )
            return

        # Compare digit strings before conversion to avoid oversized integers.
        digits = lengths[0].lstrip("0") or "0"
        if len(digits) > 5 or (
            len(digits) == 5 and digits > "16384"
        ):
            self.send_json(
                413,
                {"error": "body_too_large",
                 "message": "Maximum body size is 16384 bytes"},
            )
            return

        length = int(digits)
        if self.headers.get_content_type() != "application/json":
            self.send_json(
                415,
                {"error": "unsupported_media_type",
                 "message": "Use application/json"},
            )
            return

        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("Incomplete body")
            invoice = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=unique_json_object,
            )
        except (ValueError, RecursionError, OSError):
            self.send_json(
                400,
                {"error": "invalid_json",
                 "message": "Invalid or incomplete JSON body"},
            )
            return

        try:
            acknowledgement = accept_invoice(invoice)
        except ValueError as exc:
            conflict = (
                str(exc) == "Invoice ID already posted with different content"
            )
            self.send_json(
                409 if conflict else 422,
                {
                    "error": "invoice_conflict" if conflict else "invalid_invoice",
                    "message": str(exc),
                },
            )
            return
        except (sqlite3.Error, OSError):
            self.send_json(
                503,
                {"error": "storage_unavailable",
                 "message": "Accounting storage is unavailable"},
            )
            return
        except Exception:
            self.send_json(
                500,
                {"error": "internal_error",
                 "message": "Unexpected server error"},
            )
            return

        self.send_json(
            201 if acknowledgement["result"] == "created" else 200,
            acknowledgement,
        )

def main():
    with ThreadingHTTPServer(
        ("127.0.0.1", 8001), AccountingHandler
    ) as server:
        print("Accounting demo: http://127.0.0.1:8001")
        print("Endpoints: GET /health; POST /v1/postings")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()