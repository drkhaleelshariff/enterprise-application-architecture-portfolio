# Qwen Prompt V4 Evaluation Review

## Run reviewed

- Evidence: [V4 evaluation](answer-evaluation-20261014T232924044393Z.json)
- Evaluated commit: f67d73be3318679f96bb5c851e6ec58eeee6a80a
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Requested thinking setting: false
- Review method: Assistant assessment against defined case expectations
  and supplied source policies.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| EVAL-001 | Pass | Correct North acknowledgement target and citation. |
| EVAL-002 | Pass | Correct South acknowledgement target and citation. |
| EVAL-003 | Pass | Valid abstention; North evidence is not applied to South. |
| EVAL-004 | Pass | Valid abstention; no compensation amount is invented. |
| EVAL-005 | Pass | States the two-business-day acknowledgement target and explains that the supplied policy does not establish a repair completion guarantee. |
| EVAL-006 | Pass | Correctly attributes both targets and includes both citations. |
| EVAL-007 | Pass | Denies identity without document permission; no provider call. |
| EVAL-008 | Pass | Denies disabled identity; no provider call. |

All eight cases meet expectations in this run.
Two passes exercise authorization without invoking the model.
This is a mixed case-suite result, not general model accuracy.

## Comparison

Qwen V2 and V3 each met seven of eight expectations.
V4 resolves the observed EVAL-005 over-abstention while retaining
the required abstentions in EVAL-003 and EVAL-004.

All six generated responses report done_reason: stop.
Model-call durations range from approximately 48 to 83 seconds.

## Recommendation

Retain Qwen with prompt V4 as the development baseline.
Keep authorization, strict response validation and failure evidence.

Freeze this configuration before evaluating additional, previously
unused cases. Include entity mismatches, unsupported amounts,
target-versus-guarantee questions and requests containing both
supported and unsupported parts.

## Limits

The prompt was refined using this suite.
Eight passes in one development run do not establish general
reliability, production readiness or prompt-injection resistance.