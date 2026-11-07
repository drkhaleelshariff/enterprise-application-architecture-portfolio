# Enterprise Knowledge and Support Application: Scope V1

Status: Design specification; not yet implemented.

All organizations, users, documents and business details below are synthetic.
These scenarios are design assumptions, not findings from real customer discovery.

## Customer problem

Property operations staff need answers from approved operating documents
without exposing another customer's information or restricted business-unit
documents. When evidence is insufficient, they need an explicit response
and an optional support-ticket draft.

## Simulated customers

| Organization ID | Synthetic organization | Entities |
|---|---|---|
| ORG-MERIDIAN | Meridian Property Services | MER-NORTH, MER-SOUTH |
| ORG-HARBOR | Harbor Property Services | HAR-CENTRAL |

Entity identifiers belong to exactly one organization.

Existing North/South fixtures remain the legacy baseline. They are not
silently relabelled or treated as proof of organization isolation.

## Initial roles

Roles belong to organization memberships, not globally to the user.

| Role | Allowed actions |
|---|---|
| reader | Ask questions, view permitted sources, manage own ticket drafts, approve own ticket submission |
| document_manager | Reader actions plus ingest, update and delete documents within granted entities |

Both roles require explicit entity grants.
Document management does not grant access to other entities or organizations.
Membership administration is initially performed by a controlled seed/admin
process, not through the web interface.
No cross-customer administrator is exposed in the initial application.

## Synthetic access matrix

| User ID | Organization | Role | Entity grants | Status |
|---|---|---|---|---|
| LAB-MER-N | ORG-MERIDIAN | reader | MER-NORTH | active |
| LAB-MER-S | ORG-MERIDIAN | reader | MER-SOUTH | active |
| LAB-MER-BOTH | ORG-MERIDIAN | reader | MER-NORTH, MER-SOUTH | active |
| LAB-MER-DOC | ORG-MERIDIAN | document_manager | MER-NORTH | active |
| LAB-HAR-C | ORG-HARBOR | reader | HAR-CENTRAL | active |
| LAB-HAR-DOC | ORG-HARBOR | document_manager | HAR-CENTRAL | active |
| LAB-MER-DISABLED | ORG-MERIDIAN | reader | MER-NORTH | disabled |
| LAB-MER-NONE | ORG-MERIDIAN | reader | none | active |

All listed users initially have one organization membership.
Unknown users and users without an active membership receive no protected data.

## Authorization rules

1. Authenticate the user before accepting protected application requests.
2. Validate active user status and active organization membership server-side.
3. Treat a client-supplied organization ID only as a requested context.
   It does not prove membership.
4. Require an entity grant within the selected organization.
5. Require the action permission associated with the membership role.
6. Require the document to be active and its current version approved for
   question answering.
7. Filter unauthorized and ineligible evidence before ranking and generation.
8. Apply equivalent checks to source views, citations, ingestion jobs,
   conversations, ticket drafts and external ticket operations.
9. Do not expose unauthorized titles, snippets, counts or citations.
10. Recheck current authorization before returning protected results or
    submitting an external action. Test revocation during in-flight work.
11. Treat document contents as evidence, never as instructions granting
    permissions or approving tool actions.
12. Historical conversations must not bypass current access rules.

Approval is tracked for an exact document version by an explicit
document-manager operation within the manager's granted entity.
Upload alone does not approve a document.
Approval does not establish that the document is factually correct.

The initial scope supports entity-level document access.
Additional per-document user grants are deferred.

## Main workflows

### Knowledge question

An authenticated user asks a question within a verified organization context.
The application retrieves permitted, approved evidence and produces a cited
answer when evidence is sufficient.

Insufficient evidence produces an explicit abstention.
Authorization failure produces a controlled denial without protected details.
Dependency failure produces an unavailable response, not an invented answer.

### Document management

A document manager uploads a supported document for a granted entity.
The application records ingestion status and a document version.
The manager explicitly approves the version before it is used for answers.

Document changes and deletions must update retrieval eligibility.
Previously prepared requests and source links must respect current access.

### Support ticket

A user requests a draft based on the current authorized conversation.
The user reviews and edits the draft.
External submission requires explicit approval of that draft version.
Editing an approved draft invalidates its approval.

Submission rechecks authorization and uses an idempotency strategy.
A network timeout with an uncertain outcome must not trigger blind duplicate
creation.

External integration credentials and destination are scoped to the organization.
The client cannot choose another organization's ticketing destination.

## Required acceptance scenarios

- Meridian North reader receives only permitted North evidence.
- Meridian South reader receives only permitted South evidence.
- Meridian both-entity reader can access both Meridian entities.
- Meridian both-entity reader cannot access Harbor data.
- Harbor users cannot access Meridian data.
- Disabled, unknown and no-entity-grant users receive no protected evidence.
- Readers cannot upload, approve, update or delete documents.
- Meridian North document manager cannot manage Meridian South documents.
- Unapproved and deleted versions do not enter answer context.
- Unsupported questions abstain without invented facts.
- Citations identify the permitted document version used.
- Direct source and conversation URLs do not bypass authorization.
- Access revocation prevents subsequent access, including conversation history.
- Retrieved instructions cannot approve or submit tickets.
- No external ticket is submitted before explicit user approval.
- Ticket submission cannot cross organization boundaries.
- Dependency failures return controlled errors without protected-data leakage.

## Delivery scope

- Python API and PostgreSQL.
- Browser login, chat, source viewing and document management.
- Ingestion, permission-aware retrieval, citations and abstention.
- One ticketing sandbox with approved submission.
- Automated deployment, operational dashboards and recovery runbook.
- Versioned evaluation and measured latency, quality, task completion and cost.

## Deferred

- Billing and payment processing.
- Autonomous ticket submission.
- Cross-customer search.
- Complex per-document user sharing.
- Production availability claims.
- Real customer data until an authorized pilot is agreed.

## Evidence rules

Keep legacy and new application results separate.
Separate controlled-provider tests from live model evaluations.
Label synthetic data, simulated customers and lab load tests.
Preserve failed and incomplete runs.
Record code version, dataset version, configuration and workload with results.
