# Direct Completion Timeout and Replay Review

## Evidence

- [Two-case diagnostic](direct-timeout-diagnostic-20261017T171030670278Z.json)
- [Diagnostic journal](direct-timeout-diagnostic-20261017T171030670278Z.jsonl)
- [Diagnostic runner log](direct-timeout-diagnostic-runner-20261017.txt)
- [Rendering-service log](direct-timeout-render-service-20261017.txt)
- [Exact-request replay](direct-replay-20261017T182236707577Z.json)
- [Replay journal](direct-replay-20261017T182236707577Z.jsonl)
- [Replay runner log](direct-replay-runner-20261017T182236707577Z.txt)
- [Full-suite review](answer-robustness-direct-no-reuse-v0405-review.md)

Diagnostic commit: 365ec8c.
Replay commit: 61a06dc.
Runtime: Ollama 0.40.5; installed runner commit 620d2225c.

Review method: Assistant assessment of requests, responses, timings,
journals, memory snapshots and service logs.
Business-owner certification was not performed.

## Method

The predefined diagnostic executes ROBUST-001 followed by ROBUST-002
once each through the live-rendering direct adapter.

The later replay sends the exact captured completion request bodies
without calling the rendering endpoint. It uses the existing direct
runner without an explicit restart or warm-up.

Both executions retain the 180-second completion timeout,
cache_prompt: false, and captured generation settings.
Neither uses automatic retries.

## Findings

| Execution | Case | Rendering duration | Completion duration | Assessment |
|---|---|---:|---:|---|
| Live rendering | ROBUST-001 | 34.96 seconds | 180.01 seconds | Completion timeout; unavailable |
| Live rendering | ROBUST-002 | 0.03 seconds | 90.58 seconds | Correct South target and citation |
| Captured replay | ROBUST-001 | Not invoked | 78.38 seconds | Correct North portal and citation |
| Captured replay | ROBUST-002 | Not invoked | 62.06 seconds | Correct South target and citation |

Durations describe client-observed HTTP stages, including response
reading and parsing. They are not model-generation time alone.

The failed diagnostic request reaches prompt processing and some
generation before cancellation. The next request starts after release.
No completed answer is available for the failed case.

Both replay completions stop at EOS without truncation.
They reuse zero prompt tokens and evaluate all 632 and 635 prompt tokens.

Replay request hashes verify and match the source request hashes.
Completed case records in each journal match its final report.

## Rendering and Residency Observations

The rendering-service log records a runner startup lasting about
34.70 seconds during the first render-only request.
The request takes about 34.96 seconds.

Thus, render-only avoids answer generation but does not avoid
model loading in this installed service path.

The diagnostic's initial memory snapshot contains one runner process.
Its final snapshot contains two runner processes with working sets
of approximately 4.9 GiB and 6.4 GiB.

A later process query shows only the direct runner and an empty Ollama
loaded-model list. The second process's command line was not captured.

During replay, Ollama's loaded-model list is empty at all recorded
checkpoints. Before and after memory snapshots contain only the
existing direct runner.

These are checkpoint observations, not continuous residency monitoring.

## Interpretation

The captured requests complete successfully without live rendering.
This supports investigating separation of prompt preparation and
generation as an operational improvement.

The evidence does not establish that concurrent model residency or
paging caused the earlier timeout. The executions differ in time,
service history and memory conditions, and their order is not
counterbalanced.

Memory snapshots and paging counters do not provide per-request,
continuous measurements of page faults or disk activity.

The earlier full-suite result remains six of eight expectations met.
Targeted replay passes do not replace its recorded execution failures.

## Recommendation

Keep the live-rendering adapter experimental and preserve all failures.

Evaluate staged prompt preparation and generation as a separate path.
Require current authorization and source-version checks before using
prepared evidence; a captured prompt is not ongoing access permission.

Preserve exact request settings, journals and strict response validation.
Define any subsequent comparison before execution.

Do not increase timeouts, add automatic retries or claim a general
performance improvement from this replay.

## Limits

Two synthetic questions in one sequential replay do not establish
repeatability, full-suite quality or production readiness.

The original baseline remains unchanged.
The unapproved injected note is excluded before generation.
No exposed-payload prompt-injection resistance is established.

Flushed journal records improve interruption recovery, but do not
guarantee survival of every write during sudden power loss.