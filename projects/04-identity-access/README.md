# Multi-Entity Identity and Access

## Status

Entity-scoped read authorization implemented.
Thirteen checks cover allowed reads, denied access and identity disabling.

A North-scoped service identity is implemented with four access and
disabling checks.

A persistent request-and-approval workflow passes eight checks,
including self-approval denial despite combined permissions.

Five additional checks verify approval boundaries and unchanged request
state after denied attempts.

A read-only access-review report distinguishes assigned permissions
from effective action scope and passes six checks.

Authentication remains simulated. Business-owner certification has
not been performed; the report remains marked not_reviewed.

All identities, roles, records and access decisions are synthetic.

## Business problem

Meridian North and Meridian South use shared applications.
Shared application usage must not automatically permit users to read
or change another entity's records.

## Objective

Demonstrate application-side authorization using trusted identity
records, explicit entity membership and action permissions.

Later stages will add service identities, separation of duties,
revocation and access review.

## Authentication and authorization

Authentication establishes who the caller is.
Authorization determines what that identity may do to a specific record.

The first version uses a simulated authenticated identity.
It does not implement passwords, tokens or an identity provider.

A caller-supplied user ID is a test input, not proof of authentication.
Roles and entity memberships come from the application's identity register,
not from caller-supplied claims.

## Initial access rules

- Deny access unless every required condition is satisfied.
- The identity must exist and be active.
- The requested action must be explicitly permitted.
- The record's entity must appear in the identity's memberships.
- The application loads record ownership from its own record store.
- Unknown identities, actions, roles or records must be denied.
- An identity disabled in the register must be denied on the next check.

## First demonstration

- North reporting service: can read North leases only; cannot write.

Use two lease records:

- LEASE-001 belongs to ENT-001.
- LEASE-002 belongs to ENT-002.

Use synthetic identities to demonstrate:

- North reader: can read North leases only.
- South reader: can read South leases only.
- Group reader: can read leases from both explicitly assigned entities.
- Disabled reader: cannot read either entity's leases.

The first role permits read access only. Write and approval actions
remain denied.

## Acceptance criteria

- Authorized same-entity reads succeed.
- Prohibited cross-entity reads are denied.
- Explicit group membership permits both entities.
- Disabled and unknown identities are denied.
- Unsupported actions are denied.
- Denial returns no protected lease content.
- Disabling an identity affects the next access check.

## Limits

This is an authorization demonstration, not an authentication system.
The initial version does not implement sessions, token revocation,
production audit storage or integration with Project 3.

Local administrators who can edit the register or code are outside
the initial threat model.

## Next step

Document the access-review procedure and authorization design decisions.
Then verify the demonstration in the separate review clone.

## Run the demonstration

From the repository root:

```bat
python scripts\authorize_lease.py USR-001 LEASE-001
python scripts\test_authorize_lease.py
python scripts\test_authorization_config.py
python scripts\test_service_authorization.py
python scripts\test_lease_change_workflow.py
python scripts\test_approval_boundaries.py
python scripts\access_review.py
python scripts\test_access_review.py
```

The first command returns the authorized North lease.
test_authorize_lease.py should report 13 passed and 0 failed.
test_authorization_config.py should report 9 passed and 0 failed.
test_service_authorization.py should report 4 passed and 0 failed.
test_lease_change_workflow.py should report 8 passed and 0 failed.
test_approval_boundaries.py should report 5 passed and 0 failed.
test_access_review.py should report 6 passed and 0 failed.

The configuration tests verify rejection of missing or malformed registers,
duplicate keys and identities, unknown references and invalid permissions.

CLI exit codes:

- 0: access allowed.
- 1: access denied.
- 2: invalid invocation or unavailable/invalid configuration.

Tests modify temporary copies; the committed identity register remains
unchanged.

## Evidence

- [Authorization results](evidence/authorization-results.txt)
- [Configuration validation results](evidence/configuration-validation-results.txt)
- [Service authorization results](evidence/service-authorization-results.txt)
- [Approval workflow results](evidence/approval-workflow-results.txt)
- [Approval policy](approval-policy.md)
- [Approval boundary results](evidence/approval-boundary-results.txt)
- [Access-review report](evidence/access-review.json)
- [Access-review checks](evidence/access-review-results.txt)