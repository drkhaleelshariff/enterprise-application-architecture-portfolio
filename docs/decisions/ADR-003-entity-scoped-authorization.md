# ADR-003: Entity-Scoped Authorization and Independent Approval

- Status: Accepted for the demonstration baseline
- Date: 2026-10-14
- Scope: Synthetic Meridian identity and access demonstration

## Context

Meridian entities share applications, but shared usage must not grant
unrestricted access to each other's records.

Human and service identities need explicit permissions and entity scope.
Sensitive change requests require independent approval.

Authentication is simulated. The design assumes the application receives
an identity identifier from a trusted authentication boundary.

## Options considered

### Option 1: Role-only authorization

Grant access based on role membership.

This expresses action permissions but cannot distinguish North records
from South records without additional scope checks.

### Option 2: Separate application deployments per entity

Isolate each entity in its own deployment.

This may provide useful boundaries but duplicates operational components.
Shared reporting and administration still require explicit controls.

### Option 3: Role permissions combined with entity membership

Check active identity status, permitted action and record ownership
on every access decision.

This supports shared applications while preserving explicit entity scope.

## Decision

Choose Option 3 for this local demonstration.

- Load roles and memberships from application-controlled registers.
- Load lease ownership from the protected record register.
- Deny unknown identities, records and unsupported actions.
- Return protected lease content only after authorization succeeds.
- Apply entity restrictions to both humans and services.
- Reload configuration for each check.
- Reject invalid configuration before returning protected content.

For change requests:

- Permit only active authorized humans to request or approve.
- Record requester identity and entity when creating the request.
- Read those values from stored request state during approval.
- Reject self-approval even when a role contains both permissions.
- Check pending status and update approval within one SQLite transaction.
- Preserve request state after denied attempts.

## Alternatives within the chosen approach

A dedicated policy engine or database-backed identity catalog could
centralize enforcement as the system grows.

JSON registers keep this small demonstration inspectable and require
no third-party packages. They are not a production identity directory.

## Consequences

### Benefits

- Roles do not automatically grant access across entities.
- Service access remains explicitly scoped.
- Disabled identities lose access on the next check.
- Self-approval is blocked independently of role separation.
- Access-review reports distinguish assignments from effective scope.

### Costs and limitations

- Authentication, credential rotation and session revocation are excluded.
- Configuration files are read separately without an atomic snapshot.
- Revocation does not cancel an operation already authorized and in progress.
- One person with multiple accounts could bypass identity-ID separation.
- Local administrators can alter code and configuration.
- The approval workflow records a decision but does not execute a lease change.
- The audit record is not tamper-resistant.
- Report generation does not constitute business-owner certification.

## Verification

Six test scripts exercise:

- Human read authorization and disabling.
- Invalid configuration rejection.
- Scoped service access and disabling.
- Independent approval and self-approval denial.
- Approval identity and entity boundaries.
- Access-review scope and flags.

The current baseline contains 45 scenario checks.

## Revisit when

- Integrating a real identity provider.
- Introducing sessions or cached authorization decisions.
- Requiring atomic policy updates or concurrent administration.
- Executing approved changes against live lease or billing records.
- Adding production audit, credential and access-review workflows.