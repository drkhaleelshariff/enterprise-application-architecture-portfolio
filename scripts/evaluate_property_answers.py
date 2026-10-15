"""Record evaluation runs without automatically judging answer quality."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from answer_property_question import answer_question
from retrieve_documents import DOCUMENT_DATA, IDENTITY_DATA

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "answer_evaluation_cases.json"
)


def repository_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def evaluate(
    provider,
    *,
    provider_id,
    provider_configuration,
    prompt_version,
    capture_provider_diagnostics=False,
    answer_function=answer_question,
    cases_path=CASES,
    identity_folder=IDENTITY_DATA,
    document_folder=DOCUMENT_DATA,
):
    """Run cases and return records awaiting human review."""
    with Path(cases_path).open(encoding="utf-8-sig") as handle:
        document = json.load(handle)

    if document.get("schema_version") != "1":
        raise ValueError("Unsupported evaluation schema")

    records = []

    for case in document["cases"]:
        calls = []

        def recorded_provider(query, context):
            evidence = json.loads(context)
            call = {
                "sources": [
                    {
                        "document_id": source["document_id"],
                        "version": source["version"],
                        "citation": source["citation"],
                    }
                    for source in evidence["sources"]
                ],
            }
            calls.append(call)

            if capture_provider_diagnostics:
                call["diagnostics"] = []
                return provider(
                    query,
                    context,
                    diagnostics=call["diagnostics"],
                )

            return provider(query, context)
        started = perf_counter()
        response = answer_function(
            case["identity_id"],
            case["question"],
            recorded_provider,
            identity_folder=identity_folder,
            document_folder=document_folder,
        )
        elapsed = perf_counter() - started

        records.append({
            "case_id": case["case_id"],
            "identity_id": case["identity_id"],
            "question": case["question"],
            "expected_behavior": case["expected_behavior"],
            "required_facts": case["required_facts"],
            "required_citations": case["required_citations"],
            "review_note": case["review_note"],
            "provider_called": bool(calls),
            "provider_call_count": len(calls),
            "provider_calls": calls,
            "response": response,
            "duration_seconds": round(elapsed, 6),
            "review": {
                "decision": "not_assessed",
                "explanation": "",
            },
        })

    return {
        "schema_version": "1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "repository_commit": repository_commit(),
        "provider_id": provider_id,
        "provider_configuration": provider_configuration,
        "prompt_version": prompt_version,
        "case_count": len(records),
        "review_status": "not_reviewed",
        "cases": records,
    }