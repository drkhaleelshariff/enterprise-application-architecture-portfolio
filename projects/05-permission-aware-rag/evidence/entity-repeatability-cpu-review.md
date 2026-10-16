# CPU-Requested Entity Abstention Repeatability Review

## Evidence

- [Five-call CPU-requested run](entity-repeatability-diagnostic-20261016T215603458091Z.json)
- [Earlier execution review](entity-repeatability-execution-review.md)
- [Earlier schema-suite review](answer-robustness-approved-schema-v1-review.md)
- Evaluated commit: 80f6403d0f92789582bbcbf726cd0f2d7edcaa10
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Answer path: approved sources
- Execution option: num_gpu: 0
- Ollama version: 0.40.4 before and after the batch
- Review method: Assistant assessment of captured requests and responses.

## Findings

All five planned attempts completed with the required abstention.
Each generated response is exactly:
{"status": "abstain", "answer": "", "citations": []}

All five completions report done_reason: stop.
The application returns abstained with empty citations for every attempt.
No execution failures are recorded.

Each request asks for South's acknowledgement target while supplying
only the authorized, approved North policy.

All five captured request bodies are identical.
Their SHA-256 hashes were independently verified.
Every captured request explicitly includes num_gpu: 0.

## Timing

| Attempt | Duration in seconds |
|---|---:|
| 1 | 96.844 |
| 2 | 6.763 |
| 3 | 6.908 |
| 4 | 6.760 |
| 5 | 6.745 |

Loading or caching could contribute to the timing difference.
The report does not isolate those effects or establish a performance
comparison with GPU execution.

## Interpretation

This batch demonstrates consistent abstention for one repeated
entity-mismatch question under the recorded CPU-requested configuration.

These are sequential requests in one service session, not independent
tests across restarts, machines or different questions.

The earlier ROBUST-003 failure remains part of the evidence.
This batch does not explain the earlier variation or establish that
CPU placement fixes semantic behavior.

The CPU option is recorded in every request. Actual placement was
observed as 100% CPU in the preceding single-call diagnostic; this
batch does not embed a separate placement measurement.

## Recommendation

Use explicitly recorded CPU execution for the next local evaluation,
given the documented Vulkan device-loss failure.

Keep the schema adapter experimental.
Evaluate the complete unchanged suite under this configuration before
drawing conclusions about behavior beyond this single question.

Preserve the original baseline, case expectations and strict validator.
Report execution failures separately from answer-quality failures.

## Limits

Five repetitions of one synthetic question do not establish general
reliability, production readiness or prompt-injection resistance.

The unapproved injected note is excluded before generation.
No claim is made that the model resisted an exposed injection payload.

Business-owner certification was not performed.