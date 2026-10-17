# Entity Predecessor Checkpoint Log Review

## Evidence

- [Server log snapshot](ollama-predecessor-server-20261017.txt)
- [Predecessor diagnostic](entity-predecessor-diagnostic-20261017T001843073596Z.json)
- [Predecessor review](entity-predecessor-review.md)

Review method: Assistant assessment of runner log entries correlated
with the recorded sequence order and request timings.

## Observations

| Target condition | Logged initial processing state | Recorded outcome |
|---|---|---|
| Isolated | Empty slot, zero cached tokens; evaluates 635 prompt tokens | Abstention |
| After North portal request | Restores a 120-token checkpoint; evaluates 515 remaining prompt tokens | Answered response violating the abstention expectation |
| After South target request | Restores a 123-token checkpoint; evaluates 512 remaining prompt tokens | Abstention |

The North and South predecessor transitions appear twice in the log
and follow the same respective restoration patterns.

The runner starts with CPU execution requested through -ngl 0.
Relevant completed requests report HTTP 200 and truncated = 0.

## Interpretation

The logs demonstrate different checkpoint-restoration paths for
the two predecessor conditions.

Checkpoint reuse occurs in both passing and failing conditions.
Its presence alone therefore does not explain the failure.

The observations support investigating request-prefix reuse and
checkpoint restoration as hypotheses. They do not establish incorrect
state restoration, cache corruption or the precise cause of the outputs.

Log tasks are correlated by sequence and timing rather than a shared
application request identifier. This limits attribution precision.

## Next Control

Verify a supported way to disable request-prefix reuse in the installed
Ollama version before changing configuration.

Distinguish request-prefix reuse, the RAM prompt cache and model residency.
A setting affecting one must not be assumed to disable all three.

Keep the model, prompt, schema, evidence and validator unchanged.
Record the exact configuration change and verify its effect in logs.

Do not treat a passing control as a production fix without further testing.

## Limits

These logs describe one local runtime and a small synthetic experiment.
They do not demonstrate unauthorized disclosure or general reliability.

ROBUST-003 remains open. The schema adapter remains experimental.

Business-owner certification was not performed.