# Lease Change Approval Policy

## Status

Proposed rules for the synthetic authorization demonstration.
Implementation pending.

## Business objective

Require independent approval before a requested lease change can
be marked approved.

This workflow records approval decisions. It will not modify lease
records or create billing adjustments in its initial version.

## Permissions

- lease_change:request permits submitting a change request.
- lease_change:approve permits approving a pending request.
- lease:read remains a separate permission.

Permissions do not bypass entity restrictions.

## Request rules

- The requester must be a known active human identity.
- Its role must permit lease_change:request.
- It must belong to the entity owning the lease.
- The application determines ownership from the lease register.
- The application records requester identity and lease entity.
- A newly submitted request has status pending.

## Approval rules

- The approver must be a known active human identity.
- Its role must permit lease_change:approve.
- It must belong to the entity recorded on the request.
- The request must exist and remain pending.
- The approver must differ from the recorded requester.
- A successful approval records the approver and changes status to approved.
- Denied approval must leave the request unchanged.

## Separation of duties

Different requester and approver roles provide the usual division
of responsibilities.

The workflow must also reject self-approval even if an identity
is accidentally assigned a role containing both permissions.

Different identity IDs do not prove different people. A real deployment
must prevent one person from bypassing this rule through multiple accounts.

## Service identities

Service identities cannot request or approve changes in this version.
Their existing entity-scoped read permission remains unchanged.

## Verification plan

- Authorized request creation.
- Approval by a separate authorized person.
- Rejection of self-approval despite both permissions.
- Rejection of unauthorized or cross-entity approval.
- Rejection of disabled identities and service identities.
- Rejection of approval for unknown or already approved requests.
- Denied attempts leave stored request state unchanged.

## Limits

Authentication is simulated.
Approval does not execute the proposed change.
Credential controls and proof of independent human identity are excluded.