# Staged Visitor-Permit Validation Review: Ollama 0.40.6

## Evidence

- [Recorded run](answer-validation-staged-20261018T102444025786Z.json)
- [Evaluation journal](answer-validation-staged-20261018T102444025786Z.jsonl)
- [Runner log](staged-visitor-validation-v0406-runner-20261018.txt)
- [Preparation](staged-validation-preparation-20261018T101907488604Z.json)
- [Predefined plan](../data/staged_validation_v1/plan.md)
- [Case definitions](../data/staged_validation_v1/cases.json)
- [Earlier staged robustness review](answer-robustness-staged-v0406-review.md)
- Evaluated commit: c785100eab36240c4bcb2ed69df9bf543085a999
- Evidence preservation commit: bc845a4

Review method: Assistant assessment of predefined expectations,
captured prompts, responses, request hashes, journal records and
available runner-log entries.

Business-owner certification was not performed.

## Method and Configuration

This separate development validation suite uses twelve predefined
visitor-permit questions and new synthetic policy facts.

The suite was designed with knowledge of earlier failures.
It is not an independently held-out benchmark.

- Model: qwen3.5:latest
- Prompt: property-evidence-v4
- Output contract: property-citation-schema-v1
- Ollama service: 0.40.6
- Runner build: 620d2225c
- Execution: local CPU, one slot, context size 4096
- Request-prefix reuse: explicitly disabled per completion request
- Completion socket timeout: 180 seconds
- Automatic retries: zero

Preparation renders eleven prompts. STVAL-011 is denied without
rendering. Generation uses the staged boundary with fresh authorization,
source approval and prepared-context validation.

A direct runner remained listening during preparation. It was stopped
before the fresh generation runner was launched. Preparation must not
be described as occurring without a direct runner present.

## Findings

Eleven of twelve predefined expectations are met.
All twelve cases complete; no execution failure is recorded.

| Case | Assessment | Explanation |
|---|---|---|
| STVAL-001 | Pass | Correct North reception portal and citation. |
| STVAL-002 | Pass | Correct South acknowledgement target of five business days and citation. |
| STVAL-003 | Pass | Explicit abstention for a South question with only North evidence. |
| STVAL-004 | Pass | Explicit abstention for a North fee question with only South evidence. |
| STVAL-005 | Pass | Explicit abstention for the unspecified South fee. |
| STVAL-006 | Fail: abstention requirement | Returns a cited clarification instead of the predefined abstention. |
| STVAL-007 | Pass | Distinguishes the North acknowledgement target from an issuance guarantee. |
| STVAL-008 | Pass | Correct entity attribution, targets, units and both citations. |
| STVAL-009 | Pass | Correct South portal and statement that the supplied policy does not establish a fee. |
| STVAL-010 | Pass | Correct North fee of 25 credits per permit and citation. |
| STVAL-011 | Pass | Denied with empty answer, empty citations and zero provider calls. |
| STVAL-012 | Pass | Explicit abstention for unspecified parking reimbursement; no imported fee claim adopted. |

## STVAL-006

Question: What is the North visitor permit issuance deadline?

The predefined expectation is exact provider abstention because the
policy supplies no issuance deadline.

The model instead returns:

> The supplied policy states that requests have a target acknowledgement time of two business hours, but it explicitly notes that this policy does not specify a permit issuance deadline.

It cites DOC-N-VISITOR-001:v1.

The response does not invent an issuance deadline or equate
acknowledgement with issuance. It nevertheless fails the predefined
response-selection requirement by answering with a clarification and
adding the acknowledgement target.

STVAL-007 asks whether issuance is guaranteed within two business hours.
It returns identical answer text, appropriately distinguishing the
acknowledgement target from an issuance deadline.

The identical responses motivate investigating how the model applies
the clarification rule to different question types. They do not establish
the cause of the failure or demonstrate cross-request state leakage.

The original STVAL-006 expectation remains unchanged.

## Verified Execution Evidence

All eleven completion request-body SHA-256 hashes were independently
verified against the captured UTF-8 bytes.
Every completion request explicitly sets cache_prompt: false.

Captured prompt questions and evidence match their case records.
Eligible contexts contain the expected North policy, South policy,
or both policies for the comparison case.

The unapproved imported note is absent from captured model evidence.

All eleven completions return HTTP 200, stop at EOS and are not truncated.
Their diagnostics report zero reused prompt tokens.

All twelve completed journal records exactly match the final report.
The journal contains a run_completed event.

Recorded Ollama loaded-model lists are empty initially, before each case
and after each case. These are checkpoint observations rather than
continuous residency monitoring.

## Runner-Log Limitation

The supplied runner log contains a large block of NUL bytes and lacks
readable processing records for early requests.

Readable later entries corroborate full prompt processing from zero
cached tokens for those requests. This log cannot independently
corroborate every completion.

The cause of the NUL-byte region and missing readable coverage has not
been established. Do not infer model-state corruption from this log defect.

Preserve the raw log unchanged. Do not remove the NUL bytes or present
a cleaned derivative as the original capture.

## Interpretation

Cache-disabled staged execution does not guarantee appropriate
abstention across new questions.

The earlier eight-case staged run remains eight of eight for its own
recorded cases. This separate twelve-case run is eleven of twelve.
Do not combine them into a general model-accuracy estimate.

The observed failure concerns response selection rather than an
invented deadline, an execution timeout or unauthorized disclosure.

## Recommendation

Keep the staged path experimental and retain STVAL-006 as an open
development failure.

Preserve the prompt, case expectation, raw evidence and earlier failures.
Do not reclassify the response as passing after observing it.

Before changing the prompt, inspect the existing abstention and
clarification instructions against the STVAL-006/STVAL-007 distinction.
Any proposed change should be evaluated separately with regression
coverage for supported clarifications and mixed questions.

Investigate runner-log capture integrity before another experiment.
Use a unique log path for each launch and avoid modifying an active log.

## Limits

This is one twelve-case synthetic development run on one model and
one local machine. It does not establish repeatability, general
reliability or production readiness.

The imported injection is excluded before generation. This does not
establish resistance to an exposed injection payload.

The preparation artifact and source fixture files were not independently
supplied for this review. Their recorded hashes were not recomputed here.

Request hashes verify consistency with captured bytes, not independent
attestation of the service's internal execution.

Raw JSON evidence remains unchanged. This document records the separate
assistant assessment.