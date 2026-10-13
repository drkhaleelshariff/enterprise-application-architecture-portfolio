# ADR-001: Separate application ownership and usage

- Status: Accepted for the portfolio baseline
- Date: 2026-10-13
- Scope: Synthetic Meridian application landscape

## Context

Meridian North and Meridian South use some shared applications.

An application's owning entity is not necessarily its only user.
An application can also support several business capabilities.

The inventory must represent these relationships without duplicating
application records or confusing usage with access authorization.

## Options considered

### Option 1: One application row per served entity

Repeat an application's details for each entity that uses it.

This is easy to read initially but duplicates ownership and lifecycle
information. Updates could leave conflicting application records.

### Option 2: Lists inside application fields

Store served entities and capabilities as lists in each application row.

This keeps one row per application but requires list parsing and makes
individual references and duplicate relationships harder to validate.

### Option 3: Separate registers and relationship tables

Keep one application record with its owning entity.

Record served entities in application_entities.csv and supported
capabilities in application_capabilities.csv.

This requires multiple files but makes relationships explicit and
allows individual references and mapping pairs to be validated.

## Decision

Choose Option 3.

Use stable identifiers to link registers and relationship tables.
Keep business ownership and technical ownership in the application
register as accountable roles.

Use CSV for the initial baseline because the dataset is small,
reviewable in Git and readable with Python's standard library.

## Consequences

### Benefits

- Shared applications retain a single authoritative inventory record.
- Ownership and usage can change independently.
- Applications can support multiple capabilities.
- Invalid references and duplicate relationships can be detected.

### Costs and limitations

- Reviewers must follow relationships across several files.
- CSV provides no built-in foreign-key enforcement.
- Validation must run after inventory changes.
- Role titles do not identify named people or establish a full RACI.
- The initial model assumes one owning entity per application.
- A larger or collaboratively maintained catalog may need a database
  or dedicated architecture repository.

## Security boundary

Application usage describes business scope.

It does not authorize a user or service to access records belonging
to another entity. Record-level access controls will be demonstrated
separately in the identity and access project.

## Verification

Run from the repository root:

    python scripts/validate_inventory.py
    python scripts/test_validate_inventory.py

The checks verify references and coverage. Controlled tests verify
rejection of missing ownership and duplicate entity mappings.

These checks do not establish that the ownership assignments are
appropriate for a real organization.

## Revisit when

- An application requires joint ownership.
- Relationships require effective dates or historical tracking.
- Concurrent editing makes CSV maintenance unreliable.
- Inventory size makes manual review impractical.