# Cost Comparison Assumptions

## Status and scope

Illustrative assumptions for the synthetic Meridian scenario.
Amounts are not vendor quotes or measured expenditure.

Compare options for the four applications APP-001 through APP-004.
Include their affected interfaces within the transition estimates.

Currency: EUR.
Comparison horizon: 36 months.
No discounting, inflation, taxes or residual value is included.

## Timing convention

Transition occurs during months 1 through 6.

During these six months, the existing applications remain operational.
Their combined recurring cost is EUR 6000 per month for every option.

Target recurring costs apply during months 7 through 36.

One-time transition amounts include incremental target setup and
parallel-running costs during months 1 through 6. Do not charge these
again as target recurring costs during that period.

## Cost categories

- Monthly recurring cost: licensing or hosting plus support.
- Implementation: configuration or development.
- Data migration: profiling, mapping, trial migration and reconciliation.
- Integration change: affected interface implementation and verification.
- Training: business-user and support-team preparation.
- Parallel operation: incremental target running costs during transition.
- Retirement: archive, shutdown and contract-exit work.
- Contingency: percentage uplift applied to all one-time categories.

## Formula

One-time subtotal = implementation + data migration + integration change
+ training + parallel operation + retirement.

Transition allowance = one-time subtotal multiplied by
(1 + contingency rate).

36-month modeled cost = six months of existing recurring cost
+ transition allowance
+ thirty months of target recurring cost.

## Interpretation

Cost differences are modeled outcomes under these assumptions.
They do not establish actual savings or functional feasibility.

The consolidation estimates do not select a surviving application.
Requirements and migration gates must determine whether either
direction is feasible.

The retain option includes discovery and limited improvements.
The replace option assumes a new combined solution without selecting
a product.

## Sensitivity checks

Recalculate with:

- One-time category costs increased by 25 percent.
- Target recurring costs increased by 20 percent.
- Transition extended from six to twelve months.

For the delay scenario, hold the one-time allowance constant to isolate
recurring-cost timing. This understates delay impact if extra project
labor or parallel operation would also be required.

## Exclusions and unresolved items

- Costs of unaffected applications.
- Business disruption and opportunity costs.
- Detailed licensing and contract-exit terms.
- Costs of specific unresolved functional gaps.
- Benefits other than modeled cost differences.