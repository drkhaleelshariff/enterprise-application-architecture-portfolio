# Clarification Wording Diagnostic Review

## Evidence

- [Two-probe run](clarification-diagnostic-20261014T224118455470Z.json)
- [Three-probe run](clarification-diagnostic-20261014T225530000121Z.json)
- Model: qwen3.5:latest
- Prompt: property-evidence-v3
- Requested thinking setting: false
- Review method: Assistant assessment of captured contexts and responses.

## Findings

Both runs supplied identical authorized North policy evidence to
their probes. All captured responses report done_reason: stop.

The original guarantee question abstained in both runs.
Adding North to that question also produced abstention.
The explicit request to state the acknowledgement target and explain
its relationship to repair completion produced the required facts
and citation in both runs.

Naming the entity alone was insufficient in the observed run.
The results support sensitivity to question wording, but do not
isolate which part of the explicit clarification request mattered.

EVAL-005 remains unresolved. A successful paraphrase does not replace
the original case or change its expected behavior.

## Next experiment

Test a versioned system-prompt instruction that explicitly handles
yes-or-no guarantee questions by stating the applicable policy fact
and explaining what it does not establish.

Keep the original user question, evidence, model configuration and
validator unchanged. Test the original probe first. If it improves,
run the unchanged full suite to check for regressions.

Do not introduce automatic query rewriting based on these probes.

## Limits

These are development diagnostics, not unseen evaluation cases.
Repeated outputs do not establish general reliability or causation.