# Guarded Launcher Startup and Cleanup Review

## Evidence

- [Launch record](launcher-startup-20261105-run-ckybw2yi-final/launch.json)

- [Process start](launcher-startup-20261105-run-ckybw2yi-final/process-started.json)

- [Process finish](launcher-startup-20261105-run-ckybw2yi-final/process-finished.json)

- [Final runner log](launcher-startup-20261105-run-ckybw2yi-final/runner.log)

- [Interim snapshot](launcher-startup-20261105-run-ckybw2yi/)

- Launcher implementation commit: 43295f0

- Evidence preservation commit: d9c1aa9

Review method: Assistant assessment of operator-supplied command output.

The saved launch records and complete log were not independently

supplied for this review.

## Procedure and Observations

Before launch, the operator's checks showed no listener on port 18081,

no loaded Ollama models and no matching runner or launcher process.

The guarded launcher created run-ckybw2yi and started runner PID 13844.

The health endpoint subsequently returned status ok.

The runner was stopped externally using taskkill /PID 13844 /T /F.

This was not a successful Ctrl+C shutdown test.

After termination:

- The port check showed no listener.

- The launcher wrote process-finished.json for runner PID 13844.

- The finish record reported returncode 1 and launcher_interrupted false.

- Launcher PID 12416 was no longer running.

- The launch lock was absent.

The operator copied the completed run into the repository immediately

after shutdown. An earlier snapshot taken while the runner was active

was retained separately.

The final copied runner log measured 29,233 bytes and contained zero

NUL bytes according to the operator's byte-count command.

No answer-generation request was made as part of this check.

## Assessment

Startup and cleanup after external child termination worked in this

recorded attempt.

Return code 1 follows deliberate external termination and is not

evidence of an inference failure.

The unique log path produced a startup capture without observed NUL

bytes in this attempt. This does not establish logging integrity during

answer generation or explain the earlier damaged capture.

The interim and final directories represent one launch, not two

independent replications.

## Limits and Remaining Work

Ctrl+C handling remains unverified on the live Windows environment.

The lock coordinates instances of this launcher. It does not prevent

a manually started server from racing with the port check.

An earlier temporary run directory became unavailable before its log

could be inspected. Its log-integrity outcome remains unknown.

Preserve completed launch records promptly outside the temporary folder.

Before another model experiment, record the current runtime and use

one launcher instance with its unique run directory.

STVAL-006 remains open. This operational check does not evaluate

answer quality or resolve its abstention failure.
