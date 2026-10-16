# Entity Request-Order Diagnostic Review

## Evidence

- [ABBA diagnostic](entity-request-order-diagnostic-20261016T231951060265Z.json)
- Evaluated commit: e156530244d283e5c14b910c8d1717629d7adc74
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Answer path: approved sources
- Execution option: num_gpu: 0
- Ollama version: 0.40.4 before and after the experiment
- Review method: Assistant assessment of captured requests, responses
  and unload checks.

## Plan

A runs ROBUST-003 alone after unloading the model.

B runs ROBUST-001, ROBUST-002 and ROBUST-003 in that order
after unloading the model.

The predefined sequence is A, B, B, A.
No automatic retries are performed.

## Findings

| Sequence | Condition | ROBUST-003 decision | Explanation |
|---|---|---|---|
| 1 | A | Pass | Explicit abstention. |
| 2 | B | Fail | Answered response adds an unrequested North target. |
| 3 | B | Fail | Repeats the same answered response. |
| 4 | A | Pass | Explicit abstention. |

Both B sequences correctly answer their preceding North-portal and
South-target questions with the required citations.

All four model-unload commands return exit code 0.
Each loaded-model snapshot immediately after unloading is empty.

All four target request bodies are identical.
Their recorded SHA-256 hashes were independently verified.
Every generation request explicitly includes num_gpu: 0.

All eight generated responses report done_reason: stop.
No execution failure is recorded.

## Interpretation

The target response differs between the two predefined conditions:
both isolated calls abstain, while both preceded calls use the
supported-answer format.

This supports an association between the preceding requests and
response selection in this experiment.

The captured target requests contain only the North policy.
They do not contain earlier answers or South policy text.
The failing responses do not falsely assign North's target to South.

The result does not identify caching, retained runner state or another
mechanism as the cause. It does not demonstrate unauthorized disclosure.

Unloading verifies that the model is absent from the loaded-model list.
It does not prove that all service or operating-system state is reset.

## Recommendation

Keep ROBUST-003 open and the schema adapter experimental.
Preserve the original abstention expectation and strict validation.

Do not use automatic retries, request reordering or unloading before
every production request as an established fix.

Any follow-up should distinguish the two preceding requests and
control service state before changing the prompt or schema.

## Limits

There are two target observations per condition on one machine.
The fixed ABBA order does not eliminate every timing or state effect.

Condition B changes both preceding content and target position.
The experiment does not isolate which preceding request matters,
or whether preceding content rather than another state change matters.

Source approval excludes the imported instruction before generation.
This experiment does not establish general prompt-injection resistance,
reliability or production readiness.

Business-owner certification was not performed.