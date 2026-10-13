# Lease-to-Billing Reference Integration

## Status

Lease validation, invoice generation and SQLite persistence implemented.
Repeat instructions return the existing invoice; conflicting content
is rejected.

Accounting acknowledgement and locally simulated outage and
lost-confirmation recovery are implemented and tested.

Read-only reconciliation is implemented and tested.

The accounting HTTP server and eleven interface checks are implemented.
Billing can submit through HTTP with a finite timeout and acknowledgement
validation. Five isolated HTTP handoff checks verify connection refusal,
recovery, repeat delivery and conflict rejection.

All leases, transactions and accounting records are synthetic.

## Objective

Convert an approved lease into a billing instruction, create an invoice
and send it to a simulated accounting system.

## First demonstration

- Business entity: ENT-001.
- Lease identifier: LEASE-001.
- Billing period: 2026-11.
- Currency: EUR.
- Monthly fixed rent: 2500.00.
- Expected invoice amount: 2500.00.

Use the existing reference rent calculator.

## Build sequence

1. Validate the lease and calculate its charge.
2. Create a billing instruction and invoice.
3. Record a simulated accounting acknowledgement.
4. Add persistent storage and duplicate prevention.
5. Simulate an accounting outage and retry safely.
6. Reconcile invoices against accounting acknowledgements.
7. Introduce API contracts and separate service processes.

## Acceptance criteria

- An approved valid lease produces the expected invoice amount.
- An unapproved lease produces no billing instruction or invoice.
- Repeated delivery of one instruction creates one invoice.
- Reusing an instruction ID with different content is rejected.
- Accounting failure leaves the invoice pending.
- Retry after recovery creates one accounting posting.
- Reconciliation identifies missing accounting acknowledgements.
- Entity, lease and billing-period identifiers remain traceable.

These criteria will be demonstrated incrementally.

## Limits

The first version is a local Python workflow.
It does not demonstrate network behavior or production access controls.

Taxes, service charges, partial periods and real accounting are excluded.

This is a reference implementation, not a verified implementation of
the fictional applications in the current-state inventory.

## Run the current demonstration

From the repository root:

```bat
python scripts\test_lease_to_billing.py
python scripts\test_store_invoice.py
python scripts\test_http_lost_confirmation.py
```

Expected: two lease-validation checks and five invoice-storage checks pass.

The storage tests use a temporary database and leave the working database
unchanged.

To store the example invoice:

```bat
python scripts\store_invoice.py
```

The first delivery returns `created`. Subsequent identical deliveries
return `existing`.

The local database is stored under runtime/ and excluded from Git.

## Evidence

- [Lease validation results](evidence/lease-validation-results.txt)
- [Invoice storage results](evidence/invoice-storage-results.txt)
- [Accounting receiver results](evidence/accounting-receiver-results.txt)
- [Accounting handoff results](evidence/accounting-handoff-results.txt)
- [Reconciliation results](evidence/reconciliation-results.txt)
- [Accounting HTTP results](evidence/accounting-http-results.txt)
- [HTTP contract](http-contract.md)
- [HTTP handoff results](evidence/http-handoff-results.txt)
- [HTTP lost-confirmation recovery](evidence/http-lost-confirmation-results.txt)

## Next implementation step

Verify remaining HTTP contract cases and document the operating procedure
and architecture tradeoffs.

Lost-confirmation recovery is tested over HTTP: accounting commits,
the response is deliberately dropped, and retry retrieves the existing
posting before billing records acknowledgement.

## Reconcile the working databases

```bat
python scripts\reconcile_invoices.py
```

Exit codes:

- 0: comparison completed with no issues.
- 1: comparison completed and found inconsistencies.
- 2: comparison could not complete.

Reconciliation reports issues without repairing records.
Run it while no other process is writing: reads from the two databases
do not form a synchronized snapshot.