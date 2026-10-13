# Initial Application Rationalization Options

## Status and scope

Preliminary recommendation for the synthetic Meridian scenario.

Assess APP-001 and APP-002 as the property-register pair.
Assess APP-003 and APP-004 as the lease-system pair.

Evidence IDs refer to data/assessment_evidence.csv.
Inventory records and assumptions describe a fictional landscape.
Unknowns remain unresolved; no cost savings have been established.

## Property-register options

| Option | Potential benefit | Main constraint | Evidence |
|---|---|---|---|
| Retain both | Preserve assumed office and retail functionality while requirements are assessed | Separate records and interfaces continue to require coordination | EVD-001, EVD-002, EVD-005, EVD-006 |
| Consolidate into APP-001 | Potentially reduce application and interface maintenance | South requirements and migration feasibility are not established | EVD-001, EVD-003, EVD-006 |
| Consolidate into APP-002 | Potentially reduce application and interface maintenance | North requirements and migration feasibility are not established | EVD-002, EVD-004, EVD-005 |
| Replace both | Opportunity to select a solution against shared requirements | New implementation and migration effort; costs and product fit are unknown | EVD-003, EVD-004 |

## Lease-system options

| Option | Potential benefit | Main constraint | Evidence |
|---|---|---|---|
| Retain both | Preserve assumed office and retail workflows during assessment | Different billing handoffs remain; South uses spreadsheet calculations | EVD-007, EVD-008, EVD-009, EVD-010 |
| Consolidate into APP-003 | Potentially standardize lease administration and the billing interface | Retail rent support and cross-entity access controls are unproven | EVD-011, EVD-013 |
| Consolidate into APP-004 | Potentially standardize lease administration | Office workflow fit and long-term support are not established | EVD-009, EVD-010, EVD-014 |
| Replace both | Opportunity to address shared and entity-specific requirements together | Historical data quality and migration complexity remain unresolved | EVD-012; additional product assessment required |

## Recommendation

Retain all four applications during a bounded discovery and proof-of-concept
phase. This is an interim recommendation, not an endorsement of permanent
retention.

Test consolidation feasibility before approving a surviving application.
Keep replacement as an alternative if existing systems cannot meet
mandatory requirements at an acceptable total cost.

## Decision gates

| Gate | Required evidence | Acceptance condition |
|---|---|---|
| Functional fit | Office and retail requirements with worked examples | Mandatory requirements pass or have explicitly approved alternatives |
| Data migration | Data profile and trial migration | Required records and relationships reconcile; exceptions are resolved or approved |
| Entity access | Allowed and denied access tests | Authorized access succeeds and prohibited cross-entity access is denied |
| Integration continuity | Contract checks and transaction reconciliation | Required downstream handoffs work without unexplained missing or duplicate records |
| Economics | Comparable recurring and transition cost assumptions | Options use the same scope and time horizon; uncertainties are explicit |
| Operational readiness | Support ownership and tested recovery procedure | Accountable roles and recovery acceptance criteria are documented |

Passing a gate requires recorded evidence. An unknown is not a pass.

## Dependencies

- Property identifiers connect registers to lease systems through
  INT-001 and INT-002.
- Lease terms and billing schedules reach APP-007 through
  INT-003 and INT-004.
- Application replacement may require interface changes and identifier
  mapping across these dependencies.
- Full dependency discovery is still required. The six registered
  integrations are a limited scenario baseline, not a complete inventory.

## Retirement conditions

A displaced application may be retired only after:

- Required functions operate in the selected solution.
- Required data has been migrated or retained under an agreed policy.
- Critical records and business values have been reconciled.
- Dependent interfaces have been transferred or removed.
- Business and technical owners have accepted the transition.
- Recovery arrangements have been tested for the migration approach.

## Next step

Create a requirements comparison for both application pairs.
Use it to assess consolidation feasibility without treating unknown
capabilities as supported.