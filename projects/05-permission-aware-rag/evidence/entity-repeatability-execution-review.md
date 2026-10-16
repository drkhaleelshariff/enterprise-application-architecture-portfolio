# Entity Repeatability: Execution Failure and CPU Recovery

## Evidence

- [Five unavailable attempts](entity-repeatability-diagnostic-20261015T200929207772Z.json)
- [Single HTTP-error diagnostic](entity-repeatability-diagnostic-20261016T205043201287Z.json)
- [Ollama server log](ollama-vulkan-failure-20261017.txt)
- [Single CPU-requested diagnostic](entity-repeatability-diagnostic-20261016T214004083337Z.json)

Review method: Assistant assessment of recorded requests, responses,
diagnostics and supplied command output.
Business-owner certification was not performed.

## Findings

The initial five-call experiment returned unavailable for every attempt.
All five captured request bodies were identical and their hashes verified.
No generated-response diagnostics were captured.

A later single-call diagnostic recorded HTTP 500. Ollama reported
that an internal localhost connection closed while running the model.

The corresponding server log reports:
ggml_vulkan: device lost on Vulkan0

The log then records HTTP 500 for the generation request.
Later GPU-discovery checks time out.

The log identifies the immediate Vulkan execution failure.
It does not establish whether the underlying cause was a driver defect,
resource pressure or another backend problem. It also does not establish
that all five earlier unavailable responses had the same cause.

## CPU Diagnostic

The next single-call diagnostic explicitly requests num_gpu: 0.
The captured request and configuration both record this setting.

The supplied ollama ps output reports the model loaded on 100% CPU
with context size 4096.

The model returns the exact abstention object:
{"status": "abstain", "answer": "", "citations": []}

The application returns abstained with empty citations.
Completion reason is stop.
Recorded duration is approximately 87 seconds.

Ollama reports version 0.40.4 before and after both single-call diagnostics.

## Interpretation

CPU execution completed successfully after the documented Vulkan failure.
This supports a CPU-only repeatability experiment on this machine.

It does not establish that CPU execution fixes the earlier variation
between answered and abstained responses for ROBUST-003.

The unavailable results measure execution failure, not model abstention.
The successful single call does not establish repeatability.

The CPU placement observation was supplied separately as command output;
it is not embedded in the diagnostic JSON.

## Next Experiment

Run exactly five sequential attempts with num_gpu: 0.
Keep the model, prompt, schema, evidence, validator and timeout unchanged.

Record every outcome without automatic retries or early stopping.
Verify complete request capture, matching request bodies and their hashes.

Report execution failures separately from answer-quality findings.
Preserve earlier failures and keep the schema adapter experimental.

## Limits

The CPU diagnostic contains one attempt on one machine.
It does not establish general reliability, production readiness
or the root cause of the graphics failure.

Changing execution placement creates a different recorded configuration.
Its results must remain distinguishable from earlier runs.