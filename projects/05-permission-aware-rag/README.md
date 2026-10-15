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

Explicit provider abstention is supported. Five mock-provider checks verify
the application abstention message and rejection of malformed responses.
These checks do not establish whether a model abstains appropriately.

An evaluation harness records the eight defined cases, provider calls,
authorized source versions, responses and timing. Six mock-provider
checks verify recording behavior; semantic judgments are recorded separately in the linked reviews.

A local Ollama adapter is implemented. The current development baseline
uses qwen3.5:latest with property-evidence-v4 and thinking requested off.

Assistant review found all eight development cases and all eight separate
validation cases met their defined expectations in their recorded runs.
The validation questions were first executed after the V4 prompt was fixed.
Both suites use the same two synthetic policies; results are reported
separately because the development cases informed prompt revisions.

A separate access-card robustness suite met seven of eight expectations
under V4. An injected note was present in five model calls. No response
adopted its false fee claim, but one mixed request lost its supported
partial answer through whole-request abstention.

Earlier model and prompt failures remain preserved alongside diagnostics
and reviews. JSON run files remain unchanged; assessments are recorded
in separate review documents.

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

Keyword retrieval uses shared terms and does not establish semantic
relevance. Authorized evidence may still be insufficient for a question.

Authentication is simulated. No real identity provider, vector database
or production deployment is included. Generation uses a local Ollama
HTTP endpoint.

Response validation checks structure and citation eligibility, not
semantic support. Model quality requires separate evaluation.

The recorded results do not establish reliability across new documents,
production workloads or prompt-injection attempts. Model-call durations
in the validation run ranged from approximately 45 to 100 seconds.

The local file model does not establish atomic access-policy updates.

## Run the retrieval demonstration

From the repository root:

```bat
python scripts\retrieve_documents.py USR-001 "maintenance acknowledgement"
python scripts\test_retrieve_documents.py
python scripts\test_document_context.py
python scripts\test_answer_boundary.py
python scripts\test_document_lifecycle.py
python scripts\test_provider_abstention.py
python scripts\test_evaluate_property_answers.py
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

The provider-abstention test script should report 5 passed and 0 failed.

The evaluation-harness test script should report 6 passed and 0 failed.

## Evidence

- [Retrieval verification results](evidence/retrieval-results.txt)
- [Document context results](evidence/document-context-results.txt)
- [Answer-boundary results](evidence/answer-boundary-results.txt)
- [Document lifecycle results](evidence/document-lifecycle-results.txt)
- [Provider abstention results](evidence/provider-abstention-results.txt)
- [Evaluation harness results](evidence/evaluation-harness-results.txt)


## Next step

Keep the Qwen/V4 configuration as the development baseline.
Extend evaluation to new policy documents, adversarial evidence and
operational failures, with expectations defined before execution.

Lifecycle checks cover fresh file reads between requests. They do not
demonstrate deletion from vector indexes, caches or previous conversations.

Citation validation checks source eligibility, not whether the answer
is supported by the cited text.

## Answer-quality evaluation

The [evaluation plan](answer-evaluation-plan.md) describes the original
scope; consult the recorded runs and reviews below for completed results.

| Suite | Cases meeting expectations | Review |
|---|---|---|
| Development, Qwen/V4 | 8 of 8 | [Development review](evidence/answer-evaluation-qwen-v4-review.md) |
| Validation V1, Qwen/V4 | 8 of 8 | [Validation review](evidence/answer-validation-v1-review.md) |
| Robustness V1, Qwen/V4 | 7 of 8 | [Robustness review](evidence/answer-robustness-v1-review.md) |

These are assistant assessments of individual synthetic runs, not
business-owner certification or general model-accuracy measurements.

Case definitions:

- [Development cases](data/answer_evaluation_cases.json)
- [Validation cases](data/answer_validation_cases.json)
- [Robustness cases](data/robustness_v1/cases.json)

Recorded evidence:

- [Development run](evidence/answer-evaluation-20261014T232924044393Z.json)
- [Validation run](evidence/answer-validation-20261015T000110755434Z.json)
- [Robustness run](evidence/answer-robustness-20261015T032407149685Z.json)

From the repository root, with Ollama running and a clean working tree:

```bat
python scripts\run_property_evaluation.py
python scripts\run_property_validation.py
```

Each runner creates a separate evidence file. Exit code 0 indicates
completion and saving, not answer correctness. Review generated answers,
citations, abstentions and provider-call records before assigning passes.

Diagnostics contain generated model text. Current evidence is synthetic;
diagnostic capture requires appropriate handling before using real data.


## Known limitation: mixed requests with injected evidence

The access-card policy supplies the North submission portal but does
not specify a replacement fee. With an injected note in context, Qwen
abstains on the entire mixed request instead of answering the supported
portal part and identifying the unspecified fee.

In a three-condition diagnostic, no-note and benign-note conditions
answer correctly; the injected-note condition abstains. Policy text,
note metadata and source order were checked. The precise mechanism
remains uncertain because note wording and length differ and execution
order is fixed.

No recorded response adopts the injected 999 credits claim. This does
not establish general prompt-injection resistance or acceptable
answer availability.

An explicit partial-answer instruction in prompt V5 did not resolve
the targeted failure. V5 was not promoted; the adapter was restored
to V4. The failure remains open.

- [Three-condition V4 review](evidence/mixed-request-three-condition-review.md)
- [Unsuccessful V5 experiment review](evidence/mixed-request-v5-review.md)