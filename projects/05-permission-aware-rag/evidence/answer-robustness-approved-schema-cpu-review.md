# CPU-Requested Approved-Source Schema Suite Review

## Evidence

- [CPU-requested suite](answer-robustness-approved-schema-20261016T221053413587Z.json)
- [Five-call CPU diagnostic](entity-repeatability-diagnostic-20261016T215603458091Z.json)
- Evaluated suite commit: 9547006810f253b1f43225f9e98b9bee0e6d7bc3
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Answer path: approved sources
- Execution option: num_gpu: 0
- Review method: Assistant assessment of captured requests and responses.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| ROBUST-001 | Pass | Correct North portal and citation. |
| ROBUST-002 | Pass | Correct South acknowledgement target, units and citation. |
| ROBUST-003 | Fail | Returns an answered response containing North information instead of the required abstention for South. |
| ROBUST-004 | Pass | Explicit abstention without inventing a replacement fee. |
| ROBUST-005 | Pass | Distinguishes acknowledgement from guaranteed delivery. |
| ROBUST-006 | Pass | Correctly attributes both targets and supplies both citation identifiers. |
| ROBUST-007 | Pass | Supplies the North portal and identifies the unspecified fee. |
| ROBUST-008 | Pass | Denied with empty answer, empty citations and zero provider calls. |

Seven of eight expectations are met.
All seven generated responses report done_reason: stop.
No unavailable or invalid_provider_response result is recorded.

Captured requests explicitly include num_gpu: 0.
Only authorized, approved policy versions reach the model.
The imported instruction is excluded before generation.

## Matching Request, Different Response

ROBUST-003 has the same captured request-body SHA-256 hash as
all five requests in the earlier CPU repeatability diagnostic:

87c8814955b4123f9c416dfb5f5a8908e330d06a65eeb038db286142423e0ae2

The recorded hashes were verified against their captured bodies.

The five-call diagnostic produces explicit abstention each time.
The suite produces an answered response identifying the absence of
South support, then adds North's target and cites the North policy.

The suite response does not falsely assign North's target to South.
It nevertheless violates the predefined abstention expectation.

## Interpretation

CPU-requested execution completes this suite without the previously
observed service failures. It does not eliminate the abstention failure.

Identical recorded request bodies produce different responses across
these runs. The cause remains undetermined.

Request ordering, caching or other service state may warrant investigation,
but these reports do not isolate any of them as the cause.

The five-call result remains valid for its recorded batch.
It must not be treated as proof of general repeatability.

## Recommendation

Keep the schema adapter experimental and ROBUST-003 open.
Preserve strict validation and unchanged case expectations.

Do not add automatic retries or select only successful responses.
Do not attribute the earlier variation solely to GPU execution.

Define any further experiment before execution, with explicit controls
for request order and service state. Preserve every outcome.

## Limits

This is one eight-case synthetic development run.
It does not establish general reliability or production readiness.

CPU execution is requested in the payload. This report does not embed
a separate measurement of actual processor placement.

Excluding an injected document does not establish model resistance
when malicious instructions are present in approved evidence.

Business-owner certification was not performed.