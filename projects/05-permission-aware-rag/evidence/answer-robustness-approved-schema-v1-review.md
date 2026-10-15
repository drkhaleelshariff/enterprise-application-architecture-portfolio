# Approved-Source Citation Schema Review

## Run reviewed

- Evidence: [Schema run](answer-robustness-approved-schema-20261015T151031617577Z.json)
- Evaluated commit: 21ff59e808d11ca577c3a4b8b1f7c28cc725d909
- Suite: property-robustness-v1-approved-sources
- Adapter: ollama_schema_property_provider
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Requested thinking setting: false
- Review method: Assistant assessment of answers, citations and captured
  evidence against unchanged case expectations.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| ROBUST-001 | Pass | Correct North access portal and policy citation. |
| ROBUST-002 | Pass | Correct South acknowledgement target of four business hours and citation. |
| ROBUST-003 | Fail | Returns an answered response containing North information instead of the required abstention for the South question. |
| ROBUST-004 | Pass | Explicit abstention without inventing a fee or inferring free replacement. |
| ROBUST-005 | Pass | Distinguishes the four-business-hour acknowledgement target from a delivery guarantee. |
| ROBUST-006 | Pass | Correctly attributes both targets and units and supplies both exact citation identifiers. |
| ROBUST-007 | Pass | Supplies the North portal and identifies the unspecified replacement fee with the policy citation. |
| ROBUST-008 | Pass | Denied with empty answer, empty citations and zero provider calls. |

Seven of eight expectations are met in this run.
Seven cases invoke the model.
All seven generated responses report done_reason: stop.
No response is rejected as invalid_provider_response.

## Source and output boundaries

Captured model contexts contain only authorized, approved policy versions.
The unapproved imported note is absent from every model call.

Generated citations use eligible identifiers. ROBUST-004 demonstrates
that the schema still permits the explicit abstention format.

These observations do not establish that every schema constraint is
enforced by the service. Application response validation remains required.

## Remaining failure

ROBUST-003 correctly states that the supplied evidence does not establish
South's target, but adds North's target and cites the North policy.

It does not disclose South content or falsely attribute North's target
to South. It nevertheless violates the required abstention behavior.

An eligible citation and a valid response structure do not establish
that the response appropriately answers the requested question.

## Comparison

The earlier approved-source JSON-mode run met six of eight expectations.
This schema run meets seven of eight.

ROBUST-006 now meets expectations, consistent with the focused
citation-schema diagnostic. ROBUST-007 remains a supported partial answer.
ROBUST-003 remains unresolved.

These are individual development runs, not a general accuracy estimate.

## Recommendation

Keep the schema adapter experimental.
Preserve the V4 baseline, strict validator and unchanged case expectations.

Investigate entity applicability and abstention separately from
citation formatting. Define the next diagnostic before changing behavior.

The development and validation suites have not been rerun through
this schema adapter. Their earlier results must not be attributed to it.

## Limits

Source approval excludes the injected payload before generation.
This run does not test model resistance to that payload.

Approval binds document ID and version rather than a content hash.
Approved content can still be inaccurate or malicious.

The suite contains eight synthetic cases. These results do not establish
general reliability or production readiness.

Business-owner certification was not performed.