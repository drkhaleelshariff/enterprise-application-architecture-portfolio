# Permission-Aware Property Operations RAG

## Status

Permission-aware keyword retrieval implemented.
Nine checks verify entity filtering, permission denial, exclusion before
ranking, no-match behavior and deleted-document exclusion.

Authorized context assembly with document-version citations is implemented
and passes seven checks.

The answer-component boundary passes thirteen checks using a mock provider.
Denied and no-evidence requests skip generation. Simulated provider failures
and invalid responses return no generated answer.

A real model adapter and answer-quality evaluation remain pending.

All identities, documents and business details are synthetic.

Six lifecycle checks verify document updates, stale-citation rejection,
deletion and membership removal using temporary copies.

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

## Run the retrieval demonstration

From the repository root:

```bat
python scripts\retrieve_documents.py USR-001 "maintenance acknowledgement"
python scripts\test_retrieve_documents.py
python scripts\test_document_context.py
python scripts\test_answer_boundary.py
python scripts\test_document_lifecycle.py
```

Expected: only the North document is returned for USR-001.
The test script should report 9 passed and 0 failed.

A permitted query with no matching evidence returns no_evidence.
That retrieval status does not establish whether a natural-language
question is answerable.

The context test script should report 7 passed and 0 failed.
Denied and no-evidence results contain no context or citations.

The answer-boundary test script should report 13 passed and 0 failed.
These tests use a mock provider, not a language model.

The lifecycle test script should report 6 passed and 0 failed.

## Evidence

- [Retrieval verification results](evidence/retrieval-results.txt)
- [Document context results](evidence/document-context-results.txt)
- [Answer-boundary results](evidence/answer-boundary-results.txt)
- [Document lifecycle results](evidence/document-lifecycle-results.txt)

## Next step

Define answer-quality evaluation cases before connecting a real model.

Lifecycle checks cover fresh file reads between requests. They do not
demonstrate deletion from vector indexes, caches or previous conversations.

Citation validation checks source eligibility, not whether the answer
is supported by the cited text.