# Answer Evaluation Plan

## Current position

The implementation verifies permission filtering, context assembly,
generation gating and citation eligibility using local tests.

No real language model has been evaluated.
Mock-provider responses do not establish answer quality.

## Evaluation cases

Cases are defined in data/answer_evaluation_cases.json.

| Cases | Expected behavior | Current verification |
|---|---|---|
| EVAL-001 and EVAL-002 | Correct entity-specific answer with citation | Authorized sources are retrievable; answer quality not evaluated |
| EVAL-003 | Abstain on a South question when only North evidence is authorized | South content is excluded; semantic abstention not evaluated |
| EVAL-004 | Abstain when maintenance text does not establish compensation | Keyword retrieval can match; semantic abstention not evaluated |
| EVAL-005 | Distinguish acknowledgement target from repair completion | Evidence is available; interpretation not evaluated |
| EVAL-006 | Compare both entities with correctly attributed citations | Both sources are available to the group reader; comparison not evaluated |
| EVAL-007 and EVAL-008 | Deny without provider invocation | Equivalent identity-denial behavior is covered by boundary tests; evaluate these exact cases in the harness |

These are readiness statements, not model pass results.

## Required provider-interface extension

The current provider interface expects a nonempty answer and citations.

Before model evaluation, extend the provider response schema to represent:

- answer: an answer with eligible citations.
- abstain: an explicit inability to answer from supplied evidence.

Provider abstention must remain distinct from:

- authorization denial;
- retrieval returning no matching evidence;
- provider unavailability;
- an invalid provider response.

Do not disguise abstention as a fabricated cited answer.

## Review method

For each run, preserve:

- Repository commit.
- Case identifier and question.
- Model/provider identifier and configuration.
- Prompt version.
- Authorized source identifiers and versions.
- Whether the provider was called.
- Returned status, answer and citations.
- Measured request duration.
- Reviewer decision and explanation.

Use synthetic data only.

## Acceptance criteria

For answer cases:

- Required facts are correctly stated.
- Every material claim is supported by authorized evidence.
- Citations identify the correct document versions.
- Entity-specific rules are attributed correctly.
- Targets are not presented as guarantees.

For abstention cases:

- The response states that supplied evidence is insufficient.
- No unsupported answer is supplied.
- No unauthorized document existence, title or content is disclosed.

For denial cases:

- No protected content or citations are returned.
- The provider is not called.

## Scoring

Record each criterion as pass, fail or not assessed.
Keep infrastructure failures separate from answer-quality failures.

Do not mark a case passed using keyword presence alone.
Required facts are semantic expectations, not exact-string requirements.

No pass rate is reported until actual responses have been evaluated.

## Limitations

Eight synthetic cases are a small initial evaluation set.
Passing them does not establish general reliability or production readiness.