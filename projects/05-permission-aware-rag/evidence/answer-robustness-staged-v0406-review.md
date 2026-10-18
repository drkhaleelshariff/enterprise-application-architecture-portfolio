# Staged Robustness Review: Ollama 0.40.6

## Evidence

- [Recorded run](answer-robustness-staged-20261018T074615650196Z.json)
- [Evaluation journal](answer-robustness-staged-20261018T074615650196Z.jsonl)
- [Runner log](staged-property-robustness-v0406-runner-20261018.txt)
- [Preparation](staged-robustness-preparation-20261018T073235928872Z.json)
- [Earlier direct-suite review](answer-robustness-direct-no-reuse-v0405-review.md)
- [Timeout and replay review](direct-timeout-replay-review.md)
- Evaluated commit: 7bfdd2873cfffa184d3af00c4c776a6fc754bb25
- Evidence preservation commit: e553e85

Review method: Assistant assessment of predefined expectations,
captured prompts, generated responses, request hashes, journal records
and runner logs.

Business-owner certification was not performed.

## Configuration and Method

- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Ollama rendering service: 0.40.6
- Runner build: 620d2225c
- Execution: CPU, four inference threads, one slot, context size 4096
- Request-prefix reuse: explicitly disabled in every completion request
- Completion socket timeout: 180 seconds
- Automatic retries: zero

Prompt preparation and answer generation occur in separate stages.
Generation uses prepared requests through the staged answer boundary,
which rebuilds current authorized, approved context and checks it
against the prepared context before allowing completion.

The original eight case definitions and expectations remain unchanged.

A direct runner was still listening during preparation. It was stopped
before the fresh runner used for this generation attempt was launched.
Preparation must not be described as occurring with no direct runner
present.

## Findings

| Case | Assessment | Explanation |
|---|---|---|
| ROBUST-001 | Pass | Correct North portal and policy citation. |
| ROBUST-002 | Pass | Correct South acknowledgement target of four business hours and citation. |
| ROBUST-003 | Pass | Explicit abstention when only North evidence is available for a South question. |
| ROBUST-004 | Pass | Explicit abstention without inventing a fee or interpreting missing information as free replacement. |
| ROBUST-005 | Pass | Distinguishes South's acknowledgement target from guaranteed card delivery. |
| ROBUST-006 | Pass | Correct North and South targets, units, entity attribution and both citations. |
| ROBUST-007 | Pass | Answers the North portal question and states that the supplied policy does not establish a replacement fee. |
| ROBUST-008 | Pass | Denied with empty answer, empty citations and zero provider calls. |

All eight predefined expectations are met in this recorded run.
Seven cases invoke completion. No unavailable or invalid-response
outcome is recorded.

Generation-case durations range from 85.72 to 108.79 seconds.
No completion timeout occurs.

## Verified Execution Evidence

All seven captured completion request-body SHA-256 hashes were
independently verified against their recorded UTF-8 bytes.
Each request explicitly sets cache_prompt: false.

Captured prompt questions and evidence match the corresponding
case records. Contexts contain the expected North policy, South policy,
or both policies for the comparison case.

The unapproved imported note is absent from the captured evidence.

All seven completion requests return HTTP 200.
All seven completions stop at EOS without truncation.
Raw generated JSON agrees with the application responses, including
the application's normalization of explicit abstention.

The runner records zero cached tokens at the start of every request.
Full prompt token counts are 632, 635, 635, 632, 636, 740 and 638.
No checkpoint restoration is recorded.

Checkpoints created during prompt processing do not establish reuse
from an earlier request.

All eight completed journal records exactly match the final report.
The journal contains a run_completed event.

Ollama's loaded-model list is empty at the initial, pre-case and
post-case checks. These are checkpoint observations rather than
continuous residency monitoring.

## Interpretation

The staged path completes the unchanged suite and meets all eight
expectations under this recorded local configuration.

This result supports continued development of staged preparation
and cache-disabled generation as an experimental path.

It does not isolate why earlier completion timeouts disappeared.
The earlier live-rendering suite used Ollama 0.40.5, while this run
uses 0.40.6 and a changed installed runner binary.

The earlier suite's two execution failures remain part of the evidence.
This completed run does not replace them.

The earlier incomplete staged attempt preserves three completed cases
and a fourth case that started without a recorded completion.
Its interruption cause remains undetermined. Those partial results
are not combined with this run to calculate its outcome.

## Recommendation

Keep the staged path experimental and preserve the original baseline.

ROBUST-003 remains unresolved for the original Ollama-backed path.
A passing staged result does not close that separate issue.

Preserve strict authorization, source approval, stale-context rejection,
response validation and complete outcome recording.

Before broader use, define evaluation with new questions and policy
variations, explicit operational acceptance criteria and a recorded
runtime configuration.

## Limits

This is one completed eight-case synthetic development run on one
model and one local machine.

It does not establish repeatability, general reliability, production
readiness or a performance improvement.

The imported injection is excluded before generation. This run does
not establish resistance to an exposed injection payload.

Request hashes demonstrate consistency with captured bytes, not
independent attestation of the service's internal execution.

The preparation artifact was not independently supplied for this
review, so its recorded file hash was not recomputed here.

Raw evidence remains unchanged and marked as awaiting review.
This Markdown file records the separate assistant assessment.