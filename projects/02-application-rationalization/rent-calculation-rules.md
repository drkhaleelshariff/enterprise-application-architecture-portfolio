# Rent Calculation Rules: Demonstration Scope

## Status

Synthetic rules for a small reference calculator.
These are not legal interpretations of actual leases.

The calculator will demonstrate these rules only. Its results will
not establish that APP-003 or APP-004 supports them.

## Common rules

- Currency: EUR.
- Each case covers one complete monthly billing period.
- Amounts use decimal arithmetic.
- Round the final charge to two decimal places using ROUND_HALF_UP.
- Reject missing required inputs and negative monetary inputs.
- Reject turnover rates outside the range 0 to 1.
- Reject unknown calculation types.
- Zero turnover is valid; missing turnover is not equivalent to zero.

## Fixed office rent

Monthly charge = monthly fixed rent.

No annual conversion or partial-month calculation is included.

## Retail rent

Monthly charge = the greater of:

1. Monthly minimum rent.
2. Eligible monthly turnover multiplied by the turnover rate.

This is a minimum-or-percentage rule, not minimum rent plus percentage.

Turnover rate is expressed as a decimal: 0.06 means 6 percent.

An adjustment case supplies the corrected total eligible turnover for
the period. The calculator recomputes the full period charge; it does
not generate a credit note or determine an incremental adjustment.

## Exclusions

- Taxes and service charges.
- Foreign exchange.
- Partial periods and day-count conventions.
- Annual thresholds or cumulative turnover.
- Lease approval and billing dates.
- Amendment effective-date selection.
- Credit-note processing and accounting postings.

## Verification boundary

The worked examples cover calculation behavior within LS-001 and LS-002.

They do not establish complete requirement acceptance, including
scheduling, approvals, migration, access control or recovery.