# Fresh-Process Entity Cache-Control ABBA Review

## Evidence

- [Experiment report](entity-cache-abba-20261017T134403989172Z.json)
- [Earlier direct comparison](direct-entity-cache-control-review.md)
- Evaluated commit: 2a63fea33a2ec41b22360db89d8b39fd6bcd511c
- Evidence preservation commit: b959487

The experiment report links all four raw runs, runner logs and
client outputs.

Review method: Assistant assessment of captured requests, raw responses,
effective generation settings, process records and runner logs.
Business-owner certification was not performed.

## Method

The predefined condition order is cache_on, cache_off, cache_off, cache_on.

Each sequence starts a new llama-server process and runs ROBUST-001,
the North portal question, followed by ROBUST-003, the South-target
question supplied with only authorized, approved North evidence.

The runner uses the same model blob, CPU execution, one slot,
context size 4096, and batch and microbatch sizes of 512.
All four logs identify build b42b7e6d3 and four CPU threads.

Prompts come from the previously recorded Ollama render-only preparation.
Generated JSON passes through the existing application answer boundary.
Authorization, source approval and case expectations remain unchanged.

No automatic retries or semantic early stopping are used.

## Verified Controls

The report records a closed port before each launch, distinct process
IDs, successful health checks, process exit and port closure afterward.
Launch commands are identical across all four sequences.

All eight captured request-body hashes were independently verified.
For each corresponding case, request objects differ only in cache_prompt.
The preparation-file hash matches across the experiment and raw runs.

Runner-reported generation settings match for corresponding cases.
Raw responses agree with parsed runner records and report summaries.

All four clients exit with code 0.
All eight completions return HTTP 200, stop at EOS and are not truncated.

Runner exit code 1 follows the diagnostic's deliberate termination
after generation. It is not counted as an inference failure.

## Findings

| Sequence | Cache | ROBUST-001 | ROBUST-003 | Target tokens reused | Target tokens evaluated |
|---|---|---|---|---:|---:|
| 1 | On | Pass | Fail: answered with North information | 120 | 515 |
| 2 | Off | Pass | Pass: explicit abstention | 0 | 635 |
| 3 | Off | Pass | Pass: explicit abstention | 0 | 635 |
| 4 | On | Pass | Fail: answered with North information | 120 | 515 |

Both cache-enabled logs explicitly record restoration of a 120-token
checkpoint before target processing.

Both cache-disabled targets start from zero cached tokens and evaluate
all 635 prompt tokens. Checkpoints created during target processing
do not indicate reuse from the predecessor.

All four predecessor requests start from zero cached tokens and
evaluate all 632 prompt tokens.

## Interpretation

The cache-enabled failure returns in the final sequence after both
cache-disabled sequences pass. This strengthens the earlier comparison
by controlling runner-process lifetime and counterbalancing condition order.

Under this tested configuration, enabling request-prefix reuse changes
the target response from required abstention to an answered response
containing an unrequested North fact.

This supports a local causal effect of the cache setting on response
selection. It does not identify the precise numerical or state-handling
mechanism, or establish checkpoint corruption.

The failing responses do not falsely attribute North's target to South.
They nevertheless violate the predefined abstention expectation.
The experiment does not demonstrate unauthorized disclosure.

## Recommendation

Keep the original Ollama baseline and existing adapters unchanged.
ROBUST-003 remains unresolved for that path.

Treat direct execution with cache_prompt: false as a candidate mitigation
for this observed failure, not a general reliability guarantee.

The next implementation should be a separate experimental direct adapter
with controlled failures, explicit request settings and strict application
validation. Evaluate the complete unchanged robustness suite before
considering promotion.

Preserve all earlier failures and report execution failures separately
from answer-quality failures.

## Limits

There are two target observations per condition, one predecessor,
one target question, one model and one local machine.

Fresh runner processes do not reset every operating-system or hardware
condition. The fixed ABBA order does not eliminate every possible
time-dependent effect.

Direct requests use Ollama-rendered prompts, but complete equivalence
to every internal Ollama request field has not been established.

The unapproved injected note is excluded before generation.
This experiment does not test resistance to an exposed injection payload.

The complete suite has not been evaluated through a cache-disabled
direct adapter. No production-readiness or performance claim is made.