"""Verify request limits and storage-error responses over HTTP."""

import json
import sqlite3
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import accounting_http_server as api


def request(port, body, headers):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(
            "POST", "/v1/postings", body=body, headers=headers
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), api.AccountingHandler
    )
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    port = server.server_address[1]

    try:
        status, body = request(
            port,
            b"{}",
            {
                "Content-Type": "application/json",
                "Content-Length": "16385",
            },
        )
        require(status == 413, f"Expected 413; got {status}")
        print("PASS: oversized declared body returns HTTP 413")

        status, body = request(
            port,
            b"{}",
            {
                "Content-Type": "application/json",
                "Content-Length": "invalid",
            },
        )
        require(status == 400, f"Expected 400; got {status}")
        print("PASS: malformed length returns HTTP 400")

        status, body = request(
            port,
            b"{}",
            {
                "Content-Type": "application/json",
                "Transfer-Encoding": "chunked",
            },
        )
        require(status == 400, f"Expected 400; got {status}")
        print("PASS: unsupported transfer encoding returns HTTP 400")

        with patch.object(
            api,
            "accept_invoice",
            side_effect=sqlite3.OperationalError(
                "private database path and internal details"
            ),
        ):
            status, body = request(
                port, b"{}", {"Content-Type": "application/json"}
            )

        require(
            status == 503
            and body == {
                "error": "storage_unavailable",
                "message": "Accounting storage is unavailable",
            },
            f"Unexpected storage failure response: {status}, {body}",
        )
        print("PASS: storage failure returns sanitized HTTP 503")

        with patch.object(
            api,
            "accept_invoice",
            side_effect=RuntimeError("private internal details"),
        ):
            status, body = request(
                port, b"{}", {"Content-Type": "application/json"}
            )

        require(
            status == 500
            and body == {
                "error": "internal_error",
                "message": "Unexpected server error",
            },
            f"Unexpected server failure response: {status}, {body}",
        )
        print("PASS: unexpected failure returns sanitized HTTP 500")

    finally:
        server.shutdown()
        thread.join()
        server.server_close()

    print("\nResults: 5 passed; 0 failed")


if __name__ == "__main__":
    main()