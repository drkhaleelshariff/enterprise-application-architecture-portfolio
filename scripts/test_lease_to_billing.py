"""Check approved and unapproved lease behavior through the CLI."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "lease_to_billing.py"
DATA = ROOT / "projects" / "03-lease-to-billing" / "data"


def run_input(filename):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(DATA / filename)],
        capture_output=True,
        text=True,
        check=False,
    )


def main():
    approved = run_input("lease_001.json")

    if approved.returncode != 0 or approved.stderr:
        raise AssertionError(
            f"Approved input failed: {approved.stderr}"
        )

    actual = json.loads(approved.stdout)
    expected = {
        "schema_version": "1",
        "instruction_id": "BILL-ENT-001-LEASE-001-2026-11",
        "entity_id": "ENT-001",
        "lease_id": "LEASE-001",
        "billing_period": "2026-11",
        "currency": "EUR",
        "amount": "2500.00",
    }

    if actual != expected:
        raise AssertionError(f"Unexpected instruction: {actual}")

    print("PASS: approved lease produces the expected instruction")

    unapproved = run_input("lease_001_unapproved.json")

    if unapproved.returncode != 1:
        raise AssertionError("Unapproved input must return exit code 1")

    if unapproved.stdout.strip():
        raise AssertionError("Unapproved input produced output on stdout")

    expected_error = "FAIL: Lease is not approved; no instruction generated"
    if unapproved.stderr.strip() != expected_error:
        raise AssertionError(
            f"Unexpected rejection: {unapproved.stderr}"
        )

    print("PASS: unapproved lease is rejected without an instruction")
    print("\nResults: 2 passed; 0 failed")


if __name__ == "__main__":
    main()