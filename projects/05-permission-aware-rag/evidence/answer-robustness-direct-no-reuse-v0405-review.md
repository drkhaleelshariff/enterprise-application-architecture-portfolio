# Direct No-Reuse Robustness Review: Ollama 0.40.5

## Evidence

- [Recorded run](answer-robustness-direct-no-reuse-20261017T154610816023Z.json)
- [Runner log](direct-property-robustness-v0405-runner-20261017.txt)
- [Earlier ABBA review](entity-cache-abba-review.md)
- [Interrupted attempt log](direct-property-robustness-interrupted-20261017.txt)
- Evaluated commit: f5b99548ba341cca80c609de681e0064d920bdc2
- Evidence preservation commit: b693716

Review method: Assistant assessment of predefined expectations,
captured model inputs, generated responses, diagnostics and runner logs.
Business-owner certification was not performed.

## Configuration

- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Adapter: direct_schema_property_provider
- Adapter version: direct-schema-no-prefix-reuse-v1
- Answer path: authorized, approved source versions
- Ollama rendering service: 0.40.5
- Installed runner commit: 620d2225c
- Execution: CPU requested, context size 4096, one slot
- Request-prefix reuse: explicitly disabled per generation request
- Socket timeout: 180 seconds per HTTP stage
- Automatic retries: zero

The installed runner changed after the power-loss interruption.
Earlier ABBA experiments used Ollama 0.40.4 and runner b42b7e6d3.
Their findings remain separate from this run.

## Findings

| Case | Assessment | Explanation |
|---|---|---|
| ROBUST-001 | Fail: execution | Completion-stage timeout; application returns unavailable without an answer. |
| ROBUST-002 | Fail: execution | Completion-stage timeout; application returns unavailable without an answer. |
| ROBUST-003 | Pass | Explicit abstention for South's target when only North evidence is supplied. |
| ROBUST-004 | Pass | Explicit abstention without inventing a replacement fee. |
| ROBUST-005 | Pass | Correctly distinguishes South's acknowledgement target from guaranteed delivery. |
| ROBUST-006 | Pass | Correct North and South targets, units, attribution and both citations. |
| ROBUST-007 | Pass | Correct North portal and explicit statement that the supplied policy does not establish a fee. |
| ROBUST-008 | Pass | Denied with empty answer, empty citations and zero provider calls. |

Six of eight expectations are met in this recorded run.
Two cases fail because generation does not complete within the timeout.
Their answer quality cannot be assessed from a returned completion.

Seven cases invoke the adapter. Five produce completed generations.
No invalid_provider_response result is recorded.

## Execution Failures

Both unavailable cases successfully receive rendered prompts.
Their failures occur during the direct completion stage and record
TimeoutError, rather than rendering errors.

The runner log records cancellation of both timed-out tasks.
For the second task, cancellation is logged while processing remains
active; the task is released before the next task begins.

Client timeout and runner cancellation are separate events.
The evidence does not establish the cause of the excessive duration
or prove immediate cancellation when the client times out.

The application suppresses generated answers on these failures.
Timeouts are not counted as semantic abstentions.

## Source and Cache Boundaries

Captured contexts contain only authorized, approved policies.
The unapproved imported note is excluded before generation.

All seven completion requests explicitly set cache_prompt: false.
All fourteen captured HTTP request-body hashes were independently verified.

The five completed generations report zero reused tokens and stop
at EOS without truncation. Their full prompt token counts are
635, 632, 636, 740 and 638 respectively.

The runner log records processing from zero cached tokens for all
seven generation requests, including the two cancelled tasks.
No checkpoint restoration is recorded.

## Interpretation

ROBUST-003 meets its abstention expectation in this suite.
The completed comparison and mixed request also meet their expectations.

This does not establish an overall improvement in suite results.
Two execution failures prevent successful completion of all eight cases.

The runtime update and direct execution path differ from the earlier
Ollama-backed suite. This run does not isolate the effect of either change.

The prior ABBA experiment supports a cache-setting effect under its
own recorded configuration. This suite must not be presented as a
replication of that experiment on the updated runtime.

## Recommendation

Keep the direct adapter experimental and preserve the original baseline.

Investigate the two completion timeouts before another model run.
Do not increase timeouts or add retries merely to obtain passing results.

Improve evaluation observability and interruption recovery before
further long runs: report case progress, preserve completed case records,
and record rendering and completion durations separately.

Any follow-up should define its configuration and expectations before
execution and preserve every outcome.

## Limits

This is one eight-case synthetic development run.
It does not establish general reliability or production readiness.

The earlier attempt ended during laptop power loss and saved no
completed evaluation JSON. Its recovered runner log is preserved separately.

The imported injection is excluded before generation.
This run does not establish resistance to an exposed injection payload.

Citation eligibility and valid response structure do not establish
semantic support outside the individually reviewed cases.