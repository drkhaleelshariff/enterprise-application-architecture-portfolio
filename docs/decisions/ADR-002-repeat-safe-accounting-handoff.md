# ADR-002: Repeat-Safe Accounting Handoff

- Status: Accepted for the demonstration baseline
- Date: 2026-10-14
- Scope: Synthetic lease-to-billing integration

## Context

Billing and accounting use separate SQLite databases.

Accounting can commit a posting before its HTTP confirmation reaches
billing. A failed response therefore does not establish whether the
posting occurred.

The integration must support recovery without silently duplicating
charges or overwriting existing posting content.

## Options considered

### Option 1: One database transaction

Store billing and accounting records in one database transaction.

This simplifies atomic updates but does not demonstrate independently
owned systems or a network handoff.

### Option 2: Distributed transaction coordination

Coordinate commits across both systems.

This depends on compatible infrastructure and introduces coordination
and recovery complexity beyond this local demonstration.

### Option 3: Independent commits with repeat-safe delivery

Commit each system independently.

Use stable identifiers, reject conflicting repeats, validate acceptance
responses and reconcile the two stores.

This allows recovery from uncertain outcomes but creates temporary
differences between billing and accounting.

## Decision

Choose Option 3.

- Persist the billing invoice before submitting it.
- Identify the invoice by entity, lease and billing period.
- Accounting accepts identical repeat delivery as an existing posting.
- Accounting rejects different immutable content under the same ID.
- Return acceptance only after the accounting transaction commits.
- Billing records acknowledgement only after validating the response.
- Retry the unchanged invoice after an uncertain outcome.
- Use read-only reconciliation to identify unresolved differences.

The invoice identifier supports one base charge per lease and period.
Amendments and corrective transactions require a separate future design.

## Consequences

### Benefits

- Repeat delivery does not create another posting in the tested scenarios.
- Lost confirmation can be recovered without overwriting accounting data.
- Billing and accounting retain separate transaction boundaries.
- Conflicts and reconciliation differences are visible.

### Costs and limitations

- The two stores may temporarily disagree.
- Operators must investigate unresolved failures.
- This baseline uses manual retries without a persisted attempt history.
- Reconciliation does not provide a synchronized cross-database snapshot.
- Identifier retention and duplicate-handling rules must remain compatible.
- The demonstration does not establish exactly-once network delivery.
- Authentication, TLS and production operations are outside the baseline.

## Verification

Recorded tests cover:

- Initial acceptance and identical repeat delivery.
- Rejection of conflicting content.
- Connection refusal leaving a fresh invoice pending.
- Accounting commit followed by lost HTTP confirmation.
- Retry recovering the existing posting and acknowledging billing.
- Detection of missing postings and content differences.

See the Project 3 evidence files and operating runbook.

## Revisit when

- Lease amendments or corrective postings are introduced.
- Automated retry and attempt tracking are required.
- Multiple billing writers or higher throughput change storage needs.
- Accounting uses a real external API with different idempotency rules.
- Security and deployment requirements expand beyond local demonstration.