# Phi-3 Diagnostic Evaluation Review

## Run reviewed

- Evidence: [Diagnostic evaluation](answer-evaluation-20261014T190056110685Z.json)
- Evaluated commit: 38d503ec608feb3bc5440c50746d22fbc95200c4
- Model: phi3:mini
- Prompt: property-evidence-v1
- Review method: Assistant assessment of recorded responses and generated
  text against the defined case expectations.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| EVAL-001 | Pass | Correct North acknowledgement target and citation. |
| EVAL-002 | Pass | Correct South acknowledgement target and citation. |
| EVAL-003 | Fail | Applies North's target to a South question. The authorized citation does not support that entity attribution. |
| EVAL-004 | Fail | Generates valid JSON requesting abstention, but includes a citation. The exact abstention contract requires an empty citation list. |
| EVAL-005 | Fail | Generates abstention with invented citation DOC-N-0nerd-001:v1. Does not deliver the required acknowledgement-versus-repair clarification. |
| EVAL-006 | Pass | Correctly attributes both targets and supplies both citations. |
| EVAL-007 | Pass | Denies identity without document permission; no provider call. |
| EVAL-008 | Pass | Denies disabled identity; no provider call. |

Five of eight cases meet the defined expectations in this run.
This is a mixed case-suite result, not general model accuracy.

## Diagnostic conclusions

All six captured model responses are valid JSON and report
done_reason: stop. The two rejected responses were not rejected
because of malformed JSON or the adapter's length-completion check.

EVAL-004 violates the required abstention structure.

EVAL-005 violates the abstention structure, invents a citation and
fails to provide the expected clarification.

EVAL-003 passes structural validation but fails semantic grounding:
citation eligibility does not establish applicability to the entity
named in the question.

These diagnostics explain this run. They cannot recover the rejected
generated text from the initial run.

## Next experiment

Keep authorization and response validation unchanged.
Revise the prompt under a new prompt version to clarify entity
applicability, the exact abstention structure and how to explain
the limits of a supported policy statement.

Evaluate with the same model, options and cases.
Preserve the new run separately, whether it improves or fails.

## Limits

The same five cases meet expectations in both recorded runs.
Two runs of eight synthetic cases do not establish production
reliability. Prompt changes tested on these cases will also need
evaluation on additional, previously unused cases.