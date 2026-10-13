# Business Capabilities and Application Landscape

## Purpose

Create a traceable current-state inventory for Meridian Property
Services, a fictional property management company integrating two
business entities.

All business details, applications, roles and records are synthetic.

## Inventory scope

| Item | Count |
|---|---:|
| Business entities | 2 |
| Business capabilities | 8 |
| Business processes | 3 |
| Applications | 10 |
| Application-to-capability mappings | 10 |
| Process-to-capability mappings | 8 |
| Application-to-entity mappings | 16 |
| Directional integrations | 6 |

## Model

See the [current-state integration diagram](current-state.md).

See [ADR-001: Separate application ownership and usage](../../docs/decisions/ADR-001-separate-ownership-and-usage.md).

- Entities identify the fictional operating businesses.
- Capabilities describe what the business can do.
- Processes identify selected workflows and their primary capabilities.
- Applications record purpose, ownership and lifecycle status.
- Mapping tables record capability support and entity usage.
- Integrations record directional data flows between applications.

Application ownership and application usage are modeled separately.
Shared usage does not imply permission to access another entity's records.

Process-to-capability mappings do not establish which applications
participate in individual process steps. That detail requires explicit
process/application mapping and workflow analysis.

## Run the checks

From the repository root:

```bat
python scripts\validate_inventory.py
python scripts\test_validate_inventory.py
```

No third-party Python packages are required.

Verified locally with Python 3.13.9 on Windows.

The validator returns 0 when checks pass and 1 when inventory issues
are detected. The test runner returns a nonzero exit code if a scenario
does not behave as expected.

## Validation coverage

The validator checks:

- Expected headers and nonempty fields.
- Unique register IDs and mapping pairs.
- References to known entities, capabilities, processes and applications.
- Application capability coverage and entity usage coverage.
- Inclusion of each process's primary capability in its mappings.
- Accepted lifecycle statuses and integration mechanisms.
- Self-integrations, which are excluded from this scenario.

The test runner uses temporary inventory copies to exercise:

1. A valid baseline.
2. A missing technical owner.
3. An unknown integration target.
4. A capability without supporting applications.
5. A duplicate application/entity mapping.

## Evidence

- [Inventory validation output](evidence/inventory-validation.txt)
- [Validation test output](evidence/validation-tests.txt)

These files capture a local run. Rerun the commands to verify the
current repository state.

## Initial observations

1. Property Portfolio Management has two supporting applications.
2. Lease Management has two supporting applications.
3. Six applications serve both business entities.
4. North and South lease integrations use different mechanisms.
5. Billing and procurement feed accounting through nightly CSV imports.

These observations identify assessment questions. They do not establish
that consolidation or replacement is justified.

## Assessment questions

- Do the overlapping systems support different business requirements?
- What data must be migrated before either system can be retired?
- Is nightly transfer timely enough for the relevant business process?
- How are failed transfers and mismatched records detected and resolved?
- Who owns end-to-end recovery across application boundaries?

## Limitations

- Integration records describe assumed connections; none are implemented.
- Three processes are sampled; this is not a complete process inventory.
- All eight capabilities have application support in the baseline.
- Deliberate defects exist only in temporary test copies.
- Validation establishes structural consistency, not business suitability.
- Costs, service levels, security enforcement and recovery behavior
  have not yet been assessed.

## Next steps

Add explicit process/application participation, document the current-state
diagram and modeling decisions, then assess rationalization options.