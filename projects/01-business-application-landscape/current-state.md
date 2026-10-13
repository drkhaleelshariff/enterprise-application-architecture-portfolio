# Current-State Integration Landscape

All applications and connections are synthetic scenario assumptions.
These connections have not yet been implemented.

```mermaid
flowchart TD
    A1["APP-001 North Property Register"]
    A2["APP-002 South Property Register"]
    A3["APP-003 North Lease Manager"]
    A4["APP-004 South Lease Tracker"]
    A7["APP-007 Meridian Billing Service"]
    A8["APP-008 Meridian Procurement Portal"]
    A9["APP-009 Meridian Accounting Platform"]

    A1 -->|"INT-001: nightly CSV"| A3
    A2 -->|"INT-002: manual CSV"| A4
    A3 -->|"INT-003: REST API"| A7
    A4 -->|"INT-004: manual CSV"| A7
    A7 -->|"INT-005: nightly CSV"| A9
    A8 -->|"INT-006: nightly CSV"| A9
```

## Interpretation

Each arrow represents one directional integration from integrations.csv.
It does not establish acknowledgement, reconciliation or recovery.

Seven applications participate in the six registered integrations.

The tenant service desk, maintenance planner and workforce hub are
omitted because the current register contains no integrations for them.
This does not establish that they have no integration needs.

## Assessment questions

- Should North and South use a common lease-to-billing contract?
- What business delays result from manual or nightly transfers?
- How will failed transfers be detected and reconciled?
- How will entity identifiers be preserved through shared services?
- Which additional connections are required by the sampled processes?