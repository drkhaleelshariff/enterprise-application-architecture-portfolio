# Citation Schema Diagnostic Review

## Evidence

- [Comparison run](citation-schema-diagnostic-20261015T144550385241Z.json)
- Evaluated commit: f95d87d04b3b1bae4eac6640d29c1959698ac615
- Case: ROBUST-006
- Answer path: approved sources
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Experimental output contract: property-citation-schema-v1
- Requested thinking setting: false
- Review method: Assistant assessment of captured inputs and responses.

## Findings

| Condition | Decision | Explanation |
|---|---|---|
| JSON mode | Fail | Correct comparison, but citation values contain policy paragraphs instead of identifiers. Application validation rejects the response. |
| Citation schema | Pass | Correct North and South targets, units and exact policy citation identifiers. |

Both conditions receive identical authorized, approved policy evidence
in the same source order. Neither receives the unapproved imported note.

The runner checks that model, thinking setting, prompt version,
system prompt and explicit options match between adapters.
The requested output format differs.

Both generated responses report done_reason: stop.

## Interpretation

The schema condition resolves the observed citation-format failure
for this case in this comparison. The shared application validator
remains unchanged.

The schema restricts citation values to supplied identifiers.
It does not establish whether a claim is supported by a selected source
or whether the model should answer rather than abstain.

The schema permits both the supported-answer and abstention formats.
Appropriate abstention has not yet been evaluated through this adapter.

## Timing

Recorded durations are approximately 164 seconds for JSON mode
and 26 seconds for the schema condition.

This single comparison does not establish a performance improvement.
Execution order is fixed, and these measurements do not isolate
model loading, caching or generation time.

## Recommendation

Keep the schema adapter experimental.

Run the unchanged approved-source robustness suite through it,
preserving case expectations, source approvals, prompt and options.
Review facts, attribution, citation identifiers and abstention separately.

Do not repair invalid citations or weaken application validation.

## Limits

This is one synthetic development case and one comparison pair.
It does not establish general reliability or prompt-injection resistance.

The injected note was excluded before generation, so this comparison
does not test model behavior when exposed to that payload.

Business-owner certification was not performed.