# Entity Predecessor Diagnostic Review

## Evidence

- [Predecessor diagnostic](entity-predecessor-diagnostic-20261017T001843073596Z.json)
- [Earlier ABBA review](entity-request-order-review.md)
- Evaluated commit: 9db8551ea50983a5cc1a836ff3350dbe70e56296
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Answer path: approved sources
- Execution option: num_gpu: 0
- Ollama version: 0.40.4 before and after the experiment
- Review method: Assistant assessment of captured inputs, responses
  and unload checks.

## Plan

Each sequence starts by unloading Qwen and checking loaded models.

- A: ROBUST-003 alone.
- N: ROBUST-001 followed by ROBUST-003.
- S: ROBUST-002 followed by ROBUST-003.

The predefined order is A, N, S, S, N, A.
No automatic retries are performed.

## Findings

| Condition | Target outcomes | Assessment |
|---|---|---|
| A: no predecessor | Two explicit abstentions | Both pass. |
| N: North portal predecessor | Two answered responses adding North's target | Both fail. |
| S: South target predecessor | Two explicit abstentions | Both pass. |

The four predecessor responses meet their respective expectations,
including correct facts and citation identifiers.

All six unload commands return exit code 0.
Every loaded-model snapshot immediately after unloading is empty.

All six target request bodies are identical.
Their SHA-256 hashes were independently verified.
Every generation request includes num_gpu: 0.

All ten generated responses report done_reason: stop.
No execution failure is recorded.

## Interpretation

The North portal predecessor is associated with the target's failure
in both repetitions. The South target predecessor is followed by
appropriate abstention in both repetitions.

The target is second in both N and S. Position alone therefore does
not account for the observed difference between these conditions.

This narrows the earlier ABBA finding. The combined North-then-South
predecessors are not required to observe the failure in this run.

The mechanism remains undetermined. The two predecessor conditions
differ in question wording, evidence, identity and generated response.
The experiment does not isolate which difference matters.

Target requests contain only the authorized North policy.
They do not include preceding answers or South policy text.
The failing response does not falsely attribute North's target to South.
This experiment does not demonstrate unauthorized disclosure.

## Recommendation

Keep ROBUST-003 open and the schema adapter experimental.
Preserve strict validation and the original abstention expectation.

Do not treat request reordering, retries or model unloading as a
validated production mitigation.

Before further generation experiments, inspect available runner logs
for evidence about prompt reuse and state handling. Treat any proposed
mechanism as a hypothesis until tested with an explicit control.

## Limits

There are two target observations per condition on one machine.
Unloading does not prove that all service or operating-system state resets.

This experiment does not establish general reliability, production
readiness or prompt-injection resistance.

Business-owner certification was not performed.