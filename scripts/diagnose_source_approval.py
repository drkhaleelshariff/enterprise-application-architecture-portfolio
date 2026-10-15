"""Compare original and approved-source answer paths on one mixed request."""

import json
import subprocess
from datetime import datetime, timezone
from time import perf_counter

from answer_property_question import answer_question
from answer_approved_property_question import answer_approved_question
from evaluate_property_answers import ROOT, repository_commit
from ollama_property_provider import PROMPT_VERSION, provider
from run_property_evaluation import OUTPUT, model_metadata

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"
QUESTION = (
    "Where should North replacement access card requests be submitted, "
    "and what replacement fee applies?"
)


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
        "experiment": "original-versus-approved-source-context",
        "repository_commit": repository_commit(),
        "provider_configuration": model_metadata(),
        "prompt_version": PROMPT_VERSION,
        "identity_id": "USR-001",
        "question": QUESTION,
        "documents_file": (
            FIXTURES / "documents.json"
        ).relative_to(ROOT).as_posix(),
        "approvals_file": APPROVALS.relative_to(ROOT).as_posix(),
        "approvals_snapshot": json.loads(
            APPROVALS.read_text(encoding="utf-8-sig")
        ),
        "expected_behavior": "answer",
        "required_facts": [
            "North access portal",
            "the supplied policy does not specify a replacement fee",
        ],
        "required_citations": ["DOC-N-ACCESS-001:v1"],
        "review_status": "not_reviewed",
        "conditions": [],
    }

    for condition in ("original", "approved_sources"):
        calls = []

        def captured_provider(query, context):
            call = {
                "question": query,
                "authorized_evidence": json.loads(context),
                "diagnostics": [],
            }
            calls.append(call)
            return provider(query, context, diagnostics=call["diagnostics"])

        print(f"Running {condition}...", flush=True)
        started = perf_counter()

        if condition == "original":
            response = answer_question(
                "USR-001",
                QUESTION,
                captured_provider,
                document_folder=FIXTURES,
            )
        else:
            response = answer_approved_question(
                "USR-001",
                QUESTION,
                captured_provider,
                document_folder=FIXTURES,
                approval_path=APPROVALS,
            )

        report["conditions"].append({
            "condition": condition,
            "provider_calls": calls,
            "response": response,
            "duration_seconds": round(perf_counter() - started, 6),
        })

        print(
            json.dumps(response, ensure_ascii=False, indent=2),
            flush=True,
        )

    report["recorded_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"source-approval-diagnostic-{stamp}.json"

    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Saved: {path}")
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()