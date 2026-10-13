# Lease-to-Billing Reference Integration

## Status

Implementation pending.

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