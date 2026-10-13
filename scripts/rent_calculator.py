"""Calculate rent using the synthetic Meridian demonstration rules."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext


class RentInputError(ValueError):
    """A required calculation input is invalid."""


def nonnegative_decimal(value, field):
    if value is None or not str(value).strip():
        raise RentInputError(f"{field}: required")

    try:
        number = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise RentInputError(f"{field}: invalid decimal") from exc

    if not number.is_finite():
        raise RentInputError(f"{field}: must be finite")

    if number < 0:
        raise RentInputError(f"{field}: must be nonnegative")

    return number


def calculate_rent(
    calculation_type,
    monthly_fixed_rent=None,
    monthly_minimum_rent=None,
    eligible_turnover=None,
    turnover_rate=None,
):
    if calculation_type == "fixed":
        charge = nonnegative_decimal(
            monthly_fixed_rent, "monthly_fixed_rent"
        )

    elif calculation_type == "turnover":
        minimum = nonnegative_decimal(
            monthly_minimum_rent, "monthly_minimum_rent"
        )
        turnover = nonnegative_decimal(
            eligible_turnover, "eligible_turnover"
        )
        rate = nonnegative_decimal(turnover_rate, "turnover_rate")

        if rate > 1:
            raise RentInputError("turnover_rate: must not exceed 1")

        # Preserve sufficient precision for multiplication before rounding.
        with localcontext() as context:
            context.prec = max(
                28,
                len(turnover.as_tuple().digits)
                + len(rate.as_tuple().digits)
                + 2,
            )
            charge = max(minimum, turnover * rate)

    else:
        raise RentInputError(
            f"Unknown calculation_type: {calculation_type!r}"
        )

    with localcontext() as context:
        context.prec = max(
            28,
            len(charge.as_tuple().digits) + 2,
            charge.adjusted() + 4,
        )
        return charge.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )