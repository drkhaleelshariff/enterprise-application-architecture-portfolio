# Application Rationalization and Target-State Roadmap

## Status

Initial assessment, reference calculation demonstration, cost model,
conditional target state and gated roadmap documented.

Candidate assessments, migration and stakeholder approval remain pending.

## Business question

Should Meridian retain, consolidate or replace its overlapping property
registers and lease applications?

The current recommendation is temporary retention while mandatory
requirements, migration feasibility and operating costs are assessed.

## Reviewer route

1. Read the [assessment criteria](assessment-criteria.md).
2. Inspect the [evidence register](data/assessment_evidence.csv).
3. Review the [options assessment](options-assessment.md).
4. Read the [mandatory requirements](requirements-comparison.md).
5. Inspect the [rent rules](rent-calculation-rules.md) and
   [worked examples](data/rent_cases.csv).
6. Run the reference calculator checks.
7. Review the [cost assumptions](cost-assumptions.md) and
   [calculated scenarios](evidence/cost-comparison.txt).
8. Read the [conditional target and roadmap](target-state-roadmap.md).
9. Read the [executive brief](executive-brief.md).

## Run the demonstration

From the repository root:

```bat
python scripts\test_rent_calculator.py
```

Verified with Python 3.13.9 on Windows.
No third-party packages are required.

Expected summary:

```text
Results: 12 passed; 0 failed
```

## Calculation evidence

The cases exercise:

- Fixed monthly office rent.
- Minimum-or-percentage retail rent.
- Below-minimum, above-minimum and equal amounts.
- Zero turnover.
- Half-cent rounding using ROUND_HALF_UP.
- Recalculation using corrected turnover.
- Rejection of missing turnover, negative amounts and rates above one.

See the [captured results](evidence/rent-calculation-results.txt).

## Interpretation

The results demonstrate the reference calculator against 12 predefined
cases. They provide partial calculation evidence relevant to LS-001
and LS-002.

They do not establish that APP-003 or APP-004 meets either requirement.
Those fictional applications have not been implemented or tested.

The cases do not exhaustively test every input rule.

## Decision position

- Retain the four assessed applications during discovery.
- Evaluate consolidation in both directions.
- Consider replacement if existing systems cannot meet mandatory needs
  at an acceptable total cost.
- Keep unknowns explicit.
- Do not retire applications before migration and dependency gates pass.

## Remaining work

- Demonstrate candidate-specific requirement acceptance.
- Profile source data and perform a trial migration.
- Refine costs using candidate-specific evidence.
- Implement integration and recovery demonstrations.
- Record simulated review decisions and their rationale.
