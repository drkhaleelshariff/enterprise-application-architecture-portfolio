# Gemma Prompt V2 Evaluation Review

## Run reviewed

- Evidence: [Gemma evaluation](answer-evaluation-20261014T210102341839Z.json)
- Evaluated commit: b155e57a62276dfc3eac836efac4db30fe7b2556
- Model: gemma:2b
- Prompt: property-evidence-v2
- Review method: Assistant assessment of recorded responses and
  diagnostics against defined case expectations.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| EVAL-001 | Fail | Returns the literal phrase Supported answer; North's target is absent. |
| EVAL-002 | Fail | Returns the literal phrase Supported answer; South's target is absent. |
| EVAL-003 | Fail | Returns a placeholder answer instead of abstaining. |
| EVAL-004 | Fail | Returns a placeholder answer instead of abstaining. |
| EVAL-005 | Fail | Returns a placeholder without the acknowledgement-versus-repair clarification. |
| EVAL-006 | Fail | Both targets are absent and South's required citation is missing. |
| EVAL-007 | Pass | Denies identity without document permission; no provider call. |
| EVAL-008 | Pass | Denies disabled identity; no provider call. |

Two of eight cases meet expectations. Both passes exercise application
authorization without invoking the model.

## Diagnostic conclusions

All six model calls return the literal answer value Supported answer,
which also appears in the prompt's response example.

This suggests copying of the example value. The run does not establish
the underlying cause.

All six responses report done_reason: stop. Their structure and eligible
citations pass application validation, but their content fails evaluation.

Structural validity and citation eligibility do not establish that an
answer contains the required facts or addresses the question.

## Comparison and recommendation

Phi-3 met five of eight expectations under V2; Gemma met two of eight.
These results apply only to the recorded runs and this synthetic suite.

Do not select Gemma as the preferred provider on this evidence.
Neither tested configuration meets all case expectations.

Keep response validation unchanged. Any further model or prompt
experiment must preserve its configuration and evidence separately.

## Limits

One Gemma run does not establish general model capability.
Previously unused cases are needed to evaluate broader reliability.