"""Create an in-memory invoice from a validated synthetic lease."""

import json
import sys
from pathlib import Path

from lease_to_billing import DEFAULT_INPUT, generate_instruction


def create_invoice(lease):
    instruction = generate_instruction(lease)

    return {
        "schema_version": "1",
        "invoice_id": (
            f"INV-{instruction['entity_id']}-"
            f"{instruction['lease_id']}-{instruction['billing_period']}"
        ),
        "instruction_id": instruction["instruction_id"],
        "entity_id": instruction["entity_id"],
        "lease_id": instruction["lease_id"],
        "billing_period": instruction["billing_period"],
        "currency": instruction["currency"],
        "amount": instruction["amount"],
        "accounting_status": "pending",
    }


def main():
    if len(sys.argv) > 2:
        print(
            "Usage: python scripts/create_invoice.py [input.json]",
            file=sys.stderr,
        )
        return 1

    path = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_INPUT

    try:
        with path.open(encoding="utf-8-sig") as handle:
            lease = json.load(handle)
        invoice = create_invoice(lease)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(invoice, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())