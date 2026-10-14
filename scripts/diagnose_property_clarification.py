"""Record two clarification probes without assigning quality scores."""

import json
import subprocess
from datetime import datetime, timezone
from time import perf_counter

from answer_property_question import answer_question
from evaluate_property_answers import ROOT, repository_commit
from ollama_property_provider import PROMPT_VERSION, provider
from run_property_evaluation import OUTPUT, model_metadata

PROBES = [
    (
        "original",
        "Are routine maintenance repairs guaranteed to finish "
        "within two business days?",
    ),
    (
        "explicit_clarification",
        "For North routine maintenance, state the policy's target "
        "acknowledgement time, then explain whether that statement "
        "establishes a guaranteed repair completion time.",
    ),
]


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit working-tree changes before diagnosis")

    report = {
        "schema_version": "1",
        "experiment": "clarification-question-wording",
        "repository_commit": repository_commit(),
        "provider_configuration": model_metadata(),
        "prompt_version": PROMPT_VERSION,
        "review_status": "not_reviewed",
        "probes": [],
    }

    for probe_id, question in PROBES:
        calls = []

        def captured_provider(query, context):
            call = {
                "question": query,
                "authorized_evidence": json.loads(context),
                "diagnostics": [],
            }
            calls.append(call)
            return provider(query, context, diagnostics=call["diagnostics"])

        print(f"Running {probe_id}...", flush=True)
        started = perf_counter()
        response = answer_question("USR-001", question, captured_provider)
        record = {
            "probe_id": probe_id,
            "identity_id": "USR-001",
            "question": question,
            "provider_calls": calls,
            "response": response,
            "duration_seconds": round(perf_counter() - started, 6),
        }
        report["probes"].append(record)
        print(json.dumps(response, ensure_ascii=False, indent=2), flush=True)

    report["recorded_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"clarification-diagnostic-{stamp}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Saved: {path}")
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()