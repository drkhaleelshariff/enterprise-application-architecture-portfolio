"""Generate a billing instruction from a synthetic approved lease."""

import json
import re
import sys
from pathlib import Path

from rent_calculator import calculate_rent

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT / "projects" / "03-lease-to-billing"
    / "data" / "lease_001.json"
)

REQUIRED_FIELDS = {
    "schema_version",
    "entity_id",
    "lease_id",
    "approval_status",
    "billing_period",
    "currency",
    "calculation_type",
    "monthly_fixed_rent",
}


def generate_instruction(lease):
    if not isinstance(lease, dict):
        raise ValueError("Lease input must be a JSON object")

    if set(lease) != REQUIRED_FIELDS:
        missing = sorted(REQUIRED_FIELDS - set(lease))
        extra = sorted(set(lease) - REQUIRED_FIELDS)
        raise ValueError(f"Incorrect fields: missing={missing}; extra={extra}")

    for field in REQUIRED_FIELDS:
        value = lease[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field}: must be a nonempty string")
        if value != value.strip():
            raise ValueError(f"{field}: surrounding whitespace is not allowed")

    if lease["schema_version"] != "1":
        raise ValueError("Unsupported schema_version")

    if lease["entity_id"] not in {"ENT-001", "ENT-002"}:
        raise ValueError("Unknown entity_id")

    if not re.fullmatch(r"LEASE-[0-9]{3}", lease["lease_id"]):
        raise ValueError("lease_id must follow LEASE-001 format")

    if lease["approval_status"] != "approved":
        raise ValueError("Lease is not approved; no instruction generated")

    if not re.fullmatch(
        r"[0-9]{4}-(0[1-9]|1[0-2])", lease["billing_period"]
    ) or lease["billing_period"].startswith("0000-"):
        raise ValueError("billing_period must be a valid YYYY-MM")

    if lease["currency"] != "EUR":
        raise ValueError("This demonstration supports EUR only")

    if lease["calculation_type"] != "fixed":
        raise ValueError("This first workflow supports fixed rent only")

    if not re.fullmatch(r"[0-9]+\.[0-9]{2}", lease["monthly_fixed_rent"]):
        raise ValueError("monthly_fixed_rent must use a format such as 2500.00")

    charge = calculate_rent(
        calculation_type="fixed",
        monthly_fixed_rent=lease["monthly_fixed_rent"],
    )

    instruction_id = (
        f"BILL-{lease['entity_id']}-"
        f"{lease['lease_id']}-{lease['billing_period']}"
    )

    return {
        "schema_version": "1",
        "instruction_id": instruction_id,
        "entity_id": lease["entity_id"],
        "lease_id": lease["lease_id"],
        "billing_period": lease["billing_period"],
        "currency": lease["currency"],
        "amount": f"{charge:.2f}",
    }


def main():
    if len(sys.argv) > 2:
        print("Usage: python scripts/lease_to_billing.py [input.json]",
              file=sys.stderr)
        return 1

    path = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_INPUT

    try:
        with path.open(encoding="utf-8-sig") as handle:
            lease = json.load(handle)
        instruction = generate_instruction(lease)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(instruction, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())