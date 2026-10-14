# Enterprise Application Architecture Portfolio

An architecture portfolio for Meridian Property Services, a fictional
property management company integrating two acquired business entities.

All company details, applications, roles and data are synthetic.
This is a portfolio demonstration, not a client engagement or production system.

## Five-minute reviewer route

1. Read the [business scenario](docs/scenario.md).
2. Review the [application landscape](projects/01-business-application-landscape/README.md).
3. Inspect the [integration diagram](projects/01-business-application-landscape/current-state.md).
4. Read the [ownership and usage decision](docs/decisions/ADR-001-separate-ownership-and-usage.md).
5. Run the inventory validator and controlled-defect tests below.

## Projects

| Project | Status | Evidence |
|---|---|---|
| 1. Business capabilities and application inventory | Initial baseline implemented | Nine CSV files, validator, five test scenarios, diagram and decision record |
| 2. Rationalization and target-state roadmap | Initial assessment baseline documented | [Requirements, calculation evidence, cost sensitivities, conditional roadmap and executive brief](projects/02-application-rationalization/README.md) |
| 3. Lease-to-billing integration | Demonstration baseline implemented and verified in a separate clone | [HTTP handoff, repeat-safe posting, failure recovery, reconciliation and runbook](projects/03-lease-to-billing/README.md); 49 scenario checks across nine scripts |
| 4. Multi-entity identity and access | Demonstration baseline implemented and verified in a separate clone | [Entity authorization, scoped service identity, independent approval and access review](projects/04-identity-access/README.md); 45 checks across six scripts; authentication simulated |
| 5. Permission-aware property operations RAG | Planned | Not yet implemented |
| 6. Architecture governance and investment proposal | Planned | One modeling decision recorded; review process and proposal pending |

## Run locally

Prerequisites: Git and Python.
Verified with Python 3.13.9 on Windows.
No third-party Python packages are required for the current baseline.

From the repository root:

```bat
python scripts\validate_inventory.py
python scripts\test_validate_inventory.py
```

Both commands should finish successfully and return exit code 0.

The tests use temporary inventory copies to check rejection of missing
technical ownership, an unknown integration target, unsupported
capability coverage and duplicate entity mappings.

## What the baseline demonstrates

- Traceability between business entities, capabilities, processes and applications.
- Separation of application ownership from entity usage.
- Explicit application participation in selected processes.
- Documented directional integration dependencies.
- Automated inventory consistency checks.
- A recorded modeling decision with alternatives and consequences.

## Current limitations

The integrations are inventory records, not running connections.
The baseline does not demonstrate access enforcement, financial
correctness, recovery, production performance or measured business savings.

Multiple applications supporting a capability indicate an assessment
question; they do not by themselves justify consolidation.

## Next milestone

Build permission-aware property document retrieval, then add cited answers,
abstention, document lifecycle controls and provider-failure handling.