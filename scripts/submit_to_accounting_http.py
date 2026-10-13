"""Submit a stored billing invoice through the local accounting HTTP API."""

import json
import sqlite3
import sys
from http.client import HTTPConnection

import submit_to_accounting as handoff

HOST = "127.0.0.1"
PORT = 8001
TIMEOUT_SECONDS = 5
MAX_RESPONSE_BYTES = 16384


def accept_invoice_http(invoice, unused_database=None):
    payload = json.dumps(invoice).encode("utf-8")
    connection = HTTPConnection(HOST, PORT, timeout=TIMEOUT_SECONDS)

    try:
        connection.request(
            "POST",
            "/v1/postings",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        raw = response.read(MAX_RESPONSE_BYTES + 1)

        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Accounting response exceeds size limit")

        media_type = response.getheader("Content-Type", "")
        if media_type.split(";", 1)[0].strip().lower() != "application/json":
            raise ValueError("Accounting response is not JSON")

        acknowledgement = json.loads(raw.decode("utf-8"))

        if not isinstance(acknowledgement, dict):
            raise ValueError("Accounting response must be a JSON object")

        if response.status not in {200, 201}:
            raise ValueError(
                f"Accounting rejected request: HTTP {response.status}; "
                f"error={acknowledgement.get('error', 'unknown')}"
            )

        expected_result = "created" if response.status == 201 else "existing"
        if acknowledgement.get("result") != expected_result:
            raise ValueError("Accounting status and result disagree")

        return acknowledgement

    finally:
        connection.close()


def submit_invoice_http(instruction_id):
    return handoff.submit_invoice(
        instruction_id,
        receiver=accept_invoice_http,
    )

def main():
    if len(sys.argv) > 2:
        print(
            "Usage: python scripts/submit_to_accounting_http.py "
            "[instruction_id]",
            file=sys.stderr,
        )
        return 1

    instruction_id = (
        sys.argv[1] if len(sys.argv) == 2 else handoff.DEFAULT_ID
    )

    try:
        result = submit_invoice_http(instruction_id)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())