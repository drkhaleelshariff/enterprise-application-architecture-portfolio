# Conditional Target State and Migration Roadmap

## Status

Proposed direction for the synthetic Meridian scenario.
No surviving application or migration has been approved.

## Recommendation

Retain the four assessed applications during bounded discovery.

Evaluate a target with one shared property register and one shared
lease service, while preserving entity-specific data and authorization.

Select existing applications only if they pass the mandatory
requirements and migration gates. Consider replacement if neither
existing candidate is suitable.

Do not force both application pairs into the same decision:
property-register consolidation may be feasible even when lease-system
consolidation is not, or vice versa.

## Cost evidence

The modeled 36-month costs are:

| Option | Base modeled cost |
|---|---:|
| Retain and improve | EUR 244800 |
| Consolidate existing applications | EUR 242400 |
| Replace with combined solution | EUR 313800 |

Consolidation is EUR 2400 cheaper than retention in the base case.

It becomes more expensive than retention when one-time category costs
increase by 25 percent or transition extends to twelve months.

These figures are synthetic assumptions, not quotes or savings.
The consolidation estimate bundles both application pairs. A decision
to consolidate only one pair requires a separate cost estimate.

See cost-assumptions.md and evidence/cost-comparison.txt.

## Proposed target characteristics

- One authoritative property record per business property.
- Stable identifiers with source-to-target migration mappings.
- Explicit entity ownership on property and lease records.
- Office and retail lease requirements supported.
- Approved billing instructions delivered through a documented contract.
- Duplicate delivery does not create duplicate charges.
- Failed handoffs are detected and reconciled.
- Business and technical ownership are assigned.

These characteristics describe requirements, not implemented behavior.

## Transition stages

| Stage | Work | Exit evidence | Accountable role |
|---|---|---|---|
| 1. Discovery | Compare requirements and profile source data | Requirement gaps and data exceptions recorded | Business process owners |
| 2. Candidate assessment | Assess both consolidation directions and replacement alternatives | Mandatory requirements demonstrated or alternatives explicitly approved | Architecture lead |
| 3. Investment decision | Refine costs and choose scope | Documented recommendation and funding decision | Executive sponsor |
| 4. Trial migration | Transfer representative records and adapt interfaces | Reconciled records and verified handoffs | Data migration lead |
| 5. Pilot | Operate a bounded scope with controlled billing ownership | Access tests and transaction reconciliation pass | Application owners |
| 6. Cutover | Transfer operational authority using an approved runbook | Business acceptance and recovery readiness recorded | Change owner |
| 7. Retirement | Archive required records and remove displaced dependencies | Retention checks and shutdown acceptance completed | Application owners |

Role titles are fictional. Named accountable people would be needed
for a real migration.

## Pilot and cutover controls

- Identify the authoritative system for every pilot record.
- Permit only one system to issue live billing instructions for a lease.
- Keep shadow outputs separate from operational transactions.
- Reconcile identifiers, lease terms, charges and acknowledgements.
- Define stop conditions before the pilot starts.
- Stop on unexplained missing or duplicate charges or unauthorized access.

## Recovery boundary

Before target writes begin, recovery may use the verified source baseline.

After target writes begin, switching back requires reconciliation of
new and changed records. Restoring a backup alone is insufficient.

After accounting postings occur, recovery may require controlled
corrective transactions and finance-owner approval.

Test the recovery procedure before cutover. Do not retire the source
while an unresolved recovery dependency remains.

## Timing

The six-month transition in the cost model is a planning assumption.
It is not a validated delivery schedule.

Each stage advances only when its exit evidence is accepted.
Re-estimate costs and timing if requirements or scope change.

## Current-state preservation

APP-001 through APP-004 remain active in the inventory.
Proposed targets do not change current-state lifecycle records.

## Next implementation evidence

The lease-to-billing project will demonstrate contracts, duplicate
prevention, failure handling and reconciliation using synthetic data.

It will provide reference implementation evidence, not proof that
the existing fictional applications have passed their assessments.