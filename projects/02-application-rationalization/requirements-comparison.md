# Requirements Comparison

## Status

Proposed requirements for the synthetic Meridian scenario.
These requirements have not been approved by real business stakeholders.

No application has been demonstrated to pass them.
Existing assumptions identify candidates for assessment, not test results.

## Property-register requirements

Assess APP-001 and APP-002 against the same requirements.

| ID | Mandatory requirement | Acceptance evidence |
|---|---|---|
| PR-001 | Store office and retail properties with their required attributes | Worked examples for both property types are saved and retrieved without loss |
| PR-002 | Identify the owning business entity for every property | Records with missing or invalid entity identifiers are rejected |
| PR-003 | Preserve source identifiers during migration | Every migrated record maps to its source identifier without unexplained collisions |
| PR-004 | Provide property identifiers and attributes to lease systems | Contract checks confirm the required fields reach the correct destination |
| PR-005 | Enforce entity-specific record access | Authorized requests succeed and prohibited cross-entity requests are denied |
| PR-006 | Support reconciled data migration | Source and target records reconcile with documented handling of exceptions |

## Lease-system requirements

Assess APP-003 and APP-004 against the same requirements.

| ID | Mandatory requirement | Acceptance evidence |
|---|---|---|
| LS-001 | Support scheduled office rent charges | Approved worked examples produce the expected charge amounts and dates |
| LS-002 | Support turnover-based retail rent | Explicit calculation rules pass worked examples including adjustments and rounding |
| LS-003 | Preserve lease amendments and effective dates | Trial migration retains required amendment history and produces the expected current terms |
| LS-004 | Provide approved billing instructions | Unapproved terms are excluded and approved instructions match the agreed contract |
| LS-005 | Prevent duplicate billing instructions from creating duplicate charges | Repeated delivery of the same instruction produces one charge |
| LS-006 | Enforce entity-specific record access | Authorized requests succeed and prohibited cross-entity requests are denied |
| LS-007 | Support recovery and reconciliation after transfer failure | Missing instructions are detected and replayed without unexplained omissions or duplicates |

## Current evidence position

| Application | Existing evidence | What remains unresolved |
|---|---|---|
| APP-001 | EVD-001 and EVD-005 describe assumed office support and a registered interface | Retail fit, migration and entity-access behavior |
| APP-002 | EVD-002 and EVD-006 describe assumed retail support and a registered interface | Office fit, migration and entity-access behavior |
| APP-003 | EVD-007 and EVD-009 describe a registered API and assumed office lease support | Retail calculations, amendment handling, duplicate prevention, recovery and entity access |
| APP-004 | EVD-008 and EVD-010 describe a manual handoff and assumed retail spreadsheet calculations | Office fit, calculation controls, amendment completeness, recovery, entity access and support viability |

Evidence IDs refer to data/assessment_evidence.csv.
A registered interface does not establish that its acceptance checks pass.

## Assessment outcomes

Use one of these outcomes for each application and requirement:

- Not assessed: no assessment has been performed.
- Pass: recorded evidence demonstrates the acceptance condition.
- Fail: recorded evidence demonstrates that the condition is not met.
- Conditional: a specific change or alternative requires approval and verification.

Record the evidence reference and assessment date with every outcome.
Do not convert a synthetic assumption into a Pass.

## Decision boundary

Functional fit alone cannot authorize consolidation.

A recommendation must also address support viability, recurring and
transition costs, migration feasibility and operational readiness.
Keep recommendations separate from current application lifecycle status.

## Next step

Select a small set of worked examples for office and retail rent.
Define expected results before building the demonstration.