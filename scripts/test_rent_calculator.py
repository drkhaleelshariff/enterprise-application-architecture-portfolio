"""Verify the reference calculator against predefined CSV cases."""

import csv
from decimal import Decimal
from pathlib import Path

from rent_calculator import RentInputError, calculate_rent

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ROOT
    / "projects"
    / "02-application-rationalization"
    / "data"
    / "rent_cases.csv"
)

COLUMNS = [
    "case_id",
    "requirement_id",
    "calculation_type",
    "monthly_fixed_rent",
    "monthly_minimum_rent",
    "eligible_turnover",
    "turnover_rate",
    "expected_charge",
    "expected_outcome",
    "description",
]


def main():
    with CASES.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != COLUMNS:
            raise ValueError("Unexpected rent case headers")
        cases = list(reader)

    if not cases:
        raise ValueError("No rent cases found")

    seen = set()
    failures = 0

    for case in cases:
        case_id = case["case_id"]

        if not case_id or case_id in seen:
            raise ValueError(f"Missing or duplicate case ID: {case_id}")
        seen.add(case_id)

        if None in case or any(value is None for value in case.values()):
            raise ValueError(f"{case_id}: malformed CSV row")

        outcome = case["expected_outcome"]
        if outcome not in {"success", "error"}:
            raise ValueError(f"{case_id}: invalid expected outcome")

        if outcome == "success":
            expected = Decimal(case["expected_charge"])
            if not expected.is_finite() or expected < 0:
                raise ValueError(f"{case_id}: invalid expected charge")
        elif case["expected_charge"].strip():
            raise ValueError(
                f"{case_id}: error case must not specify a charge"
            )

        try:
            actual = calculate_rent(
                calculation_type=case["calculation_type"],
                monthly_fixed_rent=case["monthly_fixed_rent"],
                monthly_minimum_rent=case["monthly_minimum_rent"],
                eligible_turnover=case["eligible_turnover"],
                turnover_rate=case["turnover_rate"],
            )
        except RentInputError as exc:
            if outcome == "error":
                print(f"PASS: {case_id}: rejected input ({exc})")
            else:
                failures += 1
                print(f"FAIL: {case_id}: unexpected rejection ({exc})")
        else:
            if outcome == "error":
                failures += 1
                print(f"FAIL: {case_id}: expected rejection; got {actual}")
            elif actual != expected:
                failures += 1
                print(
                    f"FAIL: {case_id}: expected {expected}; got {actual}"
                )
            else:
                print(f"PASS: {case_id}: EUR {actual:.2f}")

    print(f"\nResults: {len(cases) - failures} passed; {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())