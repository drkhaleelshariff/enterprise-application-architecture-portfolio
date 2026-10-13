# Multi-Entity Identity and Access

## Status

Scope defined. Implementation pending.

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

Create the synthetic identity register and protected lease records.