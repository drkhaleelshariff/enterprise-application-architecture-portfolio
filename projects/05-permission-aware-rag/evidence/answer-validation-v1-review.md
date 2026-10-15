# Validation V1 Review

## Run reviewed

- Evidence: [Validation run](answer-validation-20261015T000110755434Z.json)
- Evaluated commit: 04a20d86b32a72ae9b86137a8a5bd604058de960
- Suite: property-validation-v1
- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Requested thinking setting: false
- Review method: Assistant assessment against case expectations and
  supplied source policies.
- Business-owner certification: Not performed.

## Findings

| Case | Decision | Explanation |
|---|---|---|
| VALID-001 | Pass | Correct North service portal and citation. |
| VALID-002 | Pass | Correct South duty manager, immediate reporting and citation. |
| VALID-003 | Pass | Abstains rather than applying South evidence to North. |
| VALID-004 | Pass | Abstains without inventing a penalty or asserting that none exists. |
| VALID-005 | Pass | States South's one-business-day acknowledgement target and explains that repair completion is not established. |
| VALID-006 | Pass | Correctly attributes both submission routes and citations. |
| VALID-007 | Pass | Supplies the North portal and explicitly identifies the unsupported compensation amount. |
| VALID-008 | Pass | Returns no_evidence with empty citations and zero provider calls. |

All eight cases meet their defined expectations.
Seven cases invoke the model; one exercises the no-evidence path.
All seven generated responses report done_reason: stop.

## Interpretation

The model configuration and prompt remained unchanged for the first
run of these new questions. Expectations were defined before execution.

The development suite and validation suite each meet all expectations
in their recorded V4 runs. Their results should remain reported
separately because the development suite informed prompt revisions.

## Recommendation

Retain Qwen with prompt V4 as the development baseline.
Keep strict validation and preserve earlier failure evidence.

Document the implementation and results before expanding testing
to new policy documents, adversarial evidence and operational failures.

## Limits

Both suites use the same two synthetic policies.
This validation does not establish reliability across new documents,
production workloads or prompt-injection attempts.

Recorded model-call durations range from approximately 45 to 100 seconds.
These measurements do not isolate model loading or generation speed.