# Qwen Prompt V2 Evaluation Review

## Run reviewed

- Evidence: [Qwen evaluation](answer-evaluation-20261014T212550493495Z.json)
- Evaluated commit: 4ac811f90a23d64cad46b09c49ccb3c060beede3
- Model: qwen3.5:latest
- Prompt: property-evidence-v2
- Requested thinking setting: false
- Review method: Assistant assessment of recorded responses and
  diagnostics against case expectations and supplied source policies.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| EVAL-001 | Pass | Correct North acknowledgement target and citation. |
| EVAL-002 | Pass | Correct South acknowledgement target and citation. |
| EVAL-003 | Pass | Valid abstention; does not apply North's policy to South or disclose unavailable documents. |
| EVAL-004 | Pass | Valid abstention; does not invent a compensation amount. |
| EVAL-005 | Fail | Valid abstention, but omits the supported acknowledgement target and required explanation that the policy does not establish repair completion. |
| EVAL-006 | Pass | Correctly attributes both targets and includes both citations. |
| EVAL-007 | Pass | Denies identity without document permission; no provider call. |
| EVAL-008 | Pass | Denies disabled identity; no provider call. |

Seven of eight cases meet expectations. Two passes exercise
authorization without invoking the model.
This is a mixed case-suite result, not general model accuracy.

## Diagnostic conclusions

All six generated responses report done_reason: stop.
No invalid provider responses occur in this run.

EVAL-005 demonstrates over-abstention against the defined expectation.
It does not invent a repair guarantee, but fails to provide the
supported clarification.

JSON key order differs in some abstentions. This is acceptable:
the validator checks the required keys and values, not their order.

The configuration records think: false as requested.
Captured diagnostics do not independently verify whether the runtime
honored that setting.

## Comparison and tradeoff

Recorded V2 results:
- Phi-3: five of eight expectations met.
- Gemma: two of eight expectations met.
- Qwen: seven of eight expectations met.

These are individual runs with different models and potentially
different model defaults, not a general benchmark.

Qwen's recorded model-call durations range from approximately
39 to 87 seconds. These durations include application and provider
work; they do not isolate generation speed or model-loading time.

Retain Qwen for the next experiment based on this suite's results.

## Next experiment

Version a prompt clarification distinguishing unsupported requests
from explanations of the limits of a supported policy statement.

Keep the model, requested thinking setting, explicit options,
case expectations, authorization and validator unchanged.
Preserve the next run separately.

## Limits

One Qwen run does not establish consistent reliability.
Prompt revisions informed by this suite require additional,
previously unused cases before broader reliability claims.