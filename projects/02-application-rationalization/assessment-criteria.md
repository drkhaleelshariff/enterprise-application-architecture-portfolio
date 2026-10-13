# Application Rationalization Assessment Criteria

## Purpose

Assess whether Meridian should retain, consolidate, replace or retire
applications in its synthetic current-state landscape.

All assessment evidence and cost assumptions are fictional and must
be labeled accordingly. Unknown information remains unknown.

## Decision options

| Option | Meaning |
|---|---|
| Retain | Continue using the application with any required improvements |
| Consolidate | Move overlapping workloads to a selected application and retire the displaced system after verification |
| Replace | Migrate to a different solution that meets documented requirements |
| Retire | Remove an application whose required functions and dependencies have been eliminated or transferred |

## Assessment criteria

| Criterion | Evidence needed | Decision relevance |
|---|---|---|
| Business fit | Required functions and documented functional gaps | Can the application support the business need? |
| Entity coverage | Entity-specific requirements and supported usage | Can a shared solution serve both entities appropriately? |
| Data suitability | Data completeness and migration constraints | Can records be transferred without unacceptable loss? |
| Integration suitability | Interfaces and downstream dependencies | What must change if the application changes? |
| Operational support | Ownership and support arrangements | Can the organization operate the application reliably? |
| Security suitability | Access requirements and known control gaps | Can required boundaries be enforced? |
| Lifecycle viability | Support status and upgrade constraints | Can the application remain maintainable? |
| Economics | Explicit recurring and transition cost assumptions | Does the option justify its full cost? |
| Migration feasibility | Delivery capacity and transition risks | Can the proposed change be executed safely? |

## Decision rules

- Similar application names or purposes do not prove redundancy.
- Unknown evidence must not be treated as a favorable assessment.
- A low recurring cost does not establish the lowest total cost.
- Migration costs include data work, integrations, training and support.
- Retirement requires dependent processes and integrations to be addressed.
- Consolidation requires the selected solution to meet both entities'
  documented requirements.
- Recommendations must identify assumptions and unresolved questions.
- Do not use a weighted score as the sole basis for a decision.

## First assessment scope

Compare:

- APP-001 North Property Register and APP-002 South Property Register.
- APP-003 North Lease Manager and APP-004 South Lease Tracker.

No application lifecycle status changes are authorized by this document.
Recommendations will be recorded separately from the current-state inventory.