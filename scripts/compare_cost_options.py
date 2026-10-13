"""Compare synthetic application options over a 36-month horizon."""

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT / "projects" / "02-application-rationalization"
    / "data" / "cost_options.csv"
)

ONE_TIME_FIELDS = [
    "implementation",
    "data_migration",
    "integration_change",
    "training",
    "parallel_operation",
    "retirement",
]

COLUMNS = [
    "option_id",
    "name",
    "current_monthly_cost",
    "target_monthly_cost",
    *ONE_TIME_FIELDS,
    "contingency_rate",
]

SCENARIOS = [
    ("Base", 6, Decimal("1"), Decimal("1")),
    ("One-time costs +25%", 6, Decimal("1.25"), Decimal("1")),
    ("Target recurring +20%", 6, Decimal("1"), Decimal("1.20")),
    ("Transition 12 months", 12, Decimal("1"), Decimal("1")),
]


def parse_number(value, field, option_id):
    if value is None or not value.strip():
        raise ValueError(f"{option_id}: missing {field}")

    try:
        number = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"{option_id}: invalid {field}") from exc

    if not number.is_finite() or number < 0:
        raise ValueError(f"{option_id}: {field} must be finite and nonnegative")

    return number


def load_options():
    with INPUT.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != COLUMNS:
            raise ValueError("Unexpected cost input headers")
        rows = list(reader)

    if not rows:
        raise ValueError("No cost options found")

    options = []
    seen = set()

    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed cost input row")

        option_id = row["option_id"].strip()
        name = row["name"].strip()

        if not option_id or not name or option_id in seen:
            raise ValueError("Missing option details or duplicate option ID")
        seen.add(option_id)

        option = {"option_id": option_id, "name": name}
        for field in COLUMNS[2:]:
            option[field] = parse_number(row[field], field, option_id)

        if option["contingency_rate"] > 1:
            raise ValueError(
                f"{option_id}: contingency rate must not exceed 1"
            )

        options.append(option)

    current_costs = {o["current_monthly_cost"] for o in options}
    if len(current_costs) != 1:
        raise ValueError("Options must use the same current cost baseline")

    return options


def calculate(option, transition_months, one_time_factor, recurring_factor):
    subtotal = sum(
        (option[field] for field in ONE_TIME_FIELDS),
        Decimal("0"),
    )
    allowance = (
        subtotal
        * one_time_factor
        * (Decimal("1") + option["contingency_rate"])
    )

    total = (
        option["current_monthly_cost"] * transition_months
        + allowance
        + option["target_monthly_cost"]
        * recurring_factor
        * (36 - transition_months)
    )

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main():
    options = load_options()

    print("Synthetic cost comparison: EUR; 36-month horizon")
    print("Scenarios vary one assumption at a time.")
    print("Delay holds one-time allowances constant.\n")

    for name, months, one_time_factor, recurring_factor in SCENARIOS:
        print(name)
        for option in options:
            total = calculate(
                option, months, one_time_factor, recurring_factor
            )
            print(f"  {option['option_id']}: EUR {total:,.2f}")
        print()

    print("Modeled costs do not establish functional feasibility or savings.")


if __name__ == "__main__":
    main()