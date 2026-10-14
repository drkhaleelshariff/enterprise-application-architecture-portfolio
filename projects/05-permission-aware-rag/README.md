# Permission-Aware Property Operations RAG

## Status

Scope defined. Implementation pending.

All identities, documents and business details are synthetic.

## Objective

Answer questions using only documents the requesting identity is
authorized to read.

First demonstrate permission-aware retrieval without a language model.
Then add cited answers, abstention and controlled provider behavior.

## Authorization boundary

- Authentication remains simulated.
- Load identity status and entity membership from Project 4.
- Require an explicit document:read permission.
- Do not treat lease:read as permission to read documents.
- Load document access metadata from application-controlled records.
- Filter unauthorized documents before ranking or assembling context.
- Unknown identities, disabled identities and invalid configuration
  must not receive protected content.
- Do not reveal unauthorized document titles, snippets or citations.

The application may load the synthetic corpus locally. Unauthorized
content must not enter ranking inputs, returned results or model context.

## Initial document scope

Use one North document and one South document.

Each document will contain:

- A stable document identifier.
- A version.
- An entity identifier.
- A title.
- Active or deleted status.
- Synthetic text.

Entity membership is the initial document access rule.
Document-specific user grants are outside the first version.

## Build stages

1. Define synthetic documents and explicit document permissions.
2. Retrieve authorized documents using local keyword matching.
3. Verify cross-entity denial and disabled-identity behavior.
4. Assemble context with document and version citations.
5. Return an explicit no-evidence response when retrieval finds no match.
6. Verify updates, deletion and membership changes affect retrieval.
7. Add a model adapter with controlled failure behavior.

## Acceptance criteria

- North users cannot retrieve South content.
- South users cannot retrieve North content.
- Explicit group membership supports both entities.
- Missing document permission results in denial.
- Disabled identities receive no document content.
- Unauthorized text is excluded before ranking and context assembly.
- Deleted documents cannot be retrieved.
- Returned citations identify the document version used.
- No matching authorized evidence produces explicit abstention.
- Provider failure does not produce an invented answer.

These criteria will be demonstrated incrementally.

## Limits

Initial keyword matching does not establish semantic retrieval quality.
A retrieval-only demonstration is not yet a complete RAG system.

No real identity provider, external model, vector database or production
deployment is included in the first stage.

The local file model does not establish atomic access-policy updates.