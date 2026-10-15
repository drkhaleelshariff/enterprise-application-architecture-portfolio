# Entity Applicability Diagnostic Review

## Evidence

- [Four-condition diagnostic](entity-applicability-diagnostic-20261015T155059735912Z.json)
- [Earlier schema suite](answer-robustness-approved-schema-20261015T151031617577Z.json)
- Evaluated diagnostic commit: 378116691535b54e02d121b4789109424f74db43
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Answer path: approved sources
- Requested thinking setting: false
- Review method: Assistant assessment of captured inputs and responses.

## Findings

| Question entity | Supplied policy | Decision | Explanation |
|---|---|---|---|
| North | North | Pass | Three-business-day acknowledgement target and correct citation. |
| South | North | Pass | Explicit abstention with empty generated answer and citations. |
| South | South | Pass | Four-business-hour acknowledgement target and correct citation. |
| North | South | Pass | Explicit abstention with empty generated answer and citations. |

All four expectations are met in this diagnostic.
Each condition invokes the provider once.
All four generated responses report done_reason: stop.

Within each identity pair, captured evidence and requested schema
remain identical while the question's entity changes.
Only authorized, approved policy evidence reaches the model.

## Comparison with the earlier failure

The South-question/North-evidence condition corresponds to ROBUST-003
in the earlier schema suite.

The recorded question, policy evidence, requested schema, model digest,
prompt version and explicit options match. The earlier response uses
the supported-answer format and includes an unrequested North fact.
This diagnostic produces the required abstention.

No prompt or schema mitigation was introduced between these results.
The passing diagnostic therefore does not establish that the earlier
failure has been fixed.

## Interpretation

The adapter can produce appropriate entity-mismatch abstention in
these conditions. Consistent behavior has not been established.

The cause of the differing outputs remains undetermined.
These reports do not capture every service or runtime condition,
nor do they contain complete serialized HTTP request bodies.

The earlier ROBUST-003 failure and suite assessment remain unchanged.

## Next diagnostic

Before changing behavior, define a bounded repeatability experiment.
Repeat the failing question with unchanged evidence and configuration,
recording every outcome rather than rerunning until a pass occurs.

Capture the complete request payload and available service-version
metadata so comparisons cover more than prompt-version labels.

Keep authorization, source approval and response validation unchanged.
Do not introduce automatic retries that conceal unsuccessful responses.

## Limits

Four synthetic conditions in one fixed execution order do not establish
general reliability or explain the variation between runs.

The imported instruction is excluded before generation.
This diagnostic does not establish prompt-injection resistance.

Business-owner certification was not performed.