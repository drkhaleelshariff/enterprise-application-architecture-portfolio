# Phi-3 Prompt V2 Evaluation Review

## Run reviewed

- Evidence: [V2 evaluation](answer-evaluation-20261014T203708626017Z.json)
- Evaluated commit: bdee247000b0d5547d5ad94337c36fa051d10841
- Model: phi3:mini
- Prompt: property-evidence-v2
- Review method: Assistant assessment of recorded responses, diagnostics
  and source documents against defined case expectations.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| EVAL-001 | Pass | Correct North acknowledgement target and citation. |
| EVAL-002 | Pass | Correct South acknowledgement target and citation. |
| EVAL-003 | Fail | Correctly recognizes that the evidence does not establish South's target, but returns the supported-answer format with North's citation instead of explicit abstention. |
| EVAL-004 | Fail | Does not invent a compensation amount, but returns the supported-answer format instead of explicit abstention. |
| EVAL-005 | Fail | Generates abstention with invented citation DOC-N-0 end:v1 and omits the required acknowledgement-versus-repair clarification. |
| EVAL-006 | Pass | Correct targets and citations. North office and South retail are supported by the source text. |
| EVAL-007 | Pass | Denies identity without document permission; no provider call. |
| EVAL-008 | Pass | Denies disabled identity; no provider call. |

Five of eight cases meet the defined expectations.
This is a mixed case-suite result, not general model accuracy.

## Comparison with V1

EVAL-003 no longer applies North's target to South. This is a content
improvement, but the required abstention contract remains unmet.

EVAL-004 communicates insufficient evidence without inventing an amount,
but the application labels it answered because it uses the answer format.

EVAL-005 remains invalid and does not deliver the required clarification.

The number of cases meeting expectations remains unchanged.

## Next experiment

Compare another installed model using the same V2 prompt, model options,
case suite, authorization pipeline and response validator.

Preserve the comparison run separately. Do not repair generated citations
or infer abstention from phrases in answer text.

## Limits

One V2 run does not establish consistent improvement.
The prompt was revised after inspecting this case suite; additional,
previously unused cases are needed before making broader reliability claims.