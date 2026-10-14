# Initial Phi-3 Answer Evaluation Review

## Run reviewed

- Evidence: [Original evaluation](answer-evaluation-20261014T163004640264Z.json)
- Evaluated commit: a38ca8bb91537941b7f91bfd5ac4954ea97b27f8
- Model: phi3:mini
- Prompt: property-evidence-v1
- Review method: Assistant assessment of recorded responses against the
  defined cases and supplied synthetic policies.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| EVAL-001 | Pass | Correct North acknowledgement target and citation; the short answer is understood in the question's context. |
| EVAL-002 | Pass | Correct South acknowledgement target and citation. |
| EVAL-003 | Fail | Answers a South question using North's two-business-day target instead of abstaining. The eligible citation does not support that entity attribution. |
| EVAL-004 | Fail | Invalid output was suppressed, but the required explicit abstention was not delivered. |
| EVAL-005 | Fail | Invalid output was suppressed; the required distinction between acknowledgement and repair completion was not delivered. |
| EVAL-006 | Pass | Correctly attributes both acknowledgement targets and includes both citations. |
| EVAL-007 | Pass | Identity without document permission is denied without a provider call. |
| EVAL-008 | Pass | Disabled identity is denied without a provider call. |

Five of eight cases meet the defined expectations in this run.
This combines answer, abstention and authorization cases; it is not
a general model-accuracy measure.

## What the evidence establishes

The recorded provider inputs contain only authorized source identifiers.
The South document is absent from EVAL-003's recorded source list.

EVAL-003 demonstrates that citation eligibility alone does not establish
whether an answer addresses the question using applicable evidence.

For EVAL-004 and EVAL-005, the application returned no generated answer.
This demonstrates suppression, not successful semantic abstention.

## Diagnostic gap

Rejected provider output was not preserved.
The exact reasons for EVAL-004 and EVAL-005 being invalid cannot be
determined from this run.

## Next action

Capture provider diagnostics in the local evaluation workflow, then
investigate rejected responses before changing the prompt or model.

Do not expose diagnostic output through the normal answer interface.

## Limits

One run of eight synthetic cases does not establish general reliability,
production readiness or resistance to prompt injection.