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

## Provider response interface

The application supports two provider response shapes.

An answer requires a nonempty answer string and eligible citations:

```json
{
  "answer": "Example answer supported by the supplied evidence.",
  "citations": ["DOC-N-001:v1"]
}
```

Explicit abstention requires exactly:

```json
{
  "status": "abstain",
  "answer": "",
  "citations": []
}
```

The application converts valid provider abstention into status abstained,
a fixed explanation and no citations. Malformed abstention responses
are suppressed as invalid_provider_response.

Five mock-provider checks verify this interface. They do not establish
whether a language model correctly recognizes insufficient evidence.

Provider abstention remains distinct from authorization denial,
retrieval returning no matching evidence, provider unavailability
and an invalid provider response.

Citation eligibility does not establish that an answer is supported
by the cited text. Semantic review remains necessary.

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