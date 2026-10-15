"""Record unchanged robustness cases through the approved-source path."""

import json
import subprocess
from datetime import datetime, timezone
from functools import partial

from answer_approved_property_question import answer_approved_question
from evaluate_property_answers import ROOT, evaluate
from ollama_schema_property_provider import (
    OUTPUT_CONTRACT_VERSION,
    PROMPT_VERSION,
    provider,
    response_schema,
)
from run_property_evaluation import OUTPUT, model_metadata
from source_approvals import load_approvals

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit working-tree changes before evaluation")

    approved = load_approvals(APPROVALS)
    configuration = model_metadata()
    captured_calls = []

    def captured_provider(query, context, *, diagnostics=None):
        evidence = json.loads(context)
        for source in evidence["sources"]:
            key = (source["document_id"], source["version"])
            if key not in approved:
                raise RuntimeError("Unapproved source reached provider")

        captured_calls.append({
            "question": query,
            "authorized_evidence": evidence,
            "requested_format": response_schema(evidence),
        })
        return provider(query, context, diagnostics=diagnostics)

    print(
        f"Running approved-source schema evaluation using "
        f"{configuration['model']}.",
        flush=True,
    )
    print("Seven cases may invoke the model. Please wait.", flush=True)

    report = evaluate(
        captured_provider,
        provider_id="ollama",
        provider_configuration=configuration,
        prompt_version=PROMPT_VERSION,
        capture_provider_diagnostics=True,
        answer_function=partial(
            answer_approved_question,
            approval_path=APPROVALS,
        ),
        cases_path=FIXTURES / "cases.json",
        document_folder=FIXTURES,
    )

    recorded_calls = [
        call
        for case in report["cases"]
        for call in case["provider_calls"]
    ]
    if len(recorded_calls) != len(captured_calls):
        raise RuntimeError("Provider input recording count mismatch")

    for recorded, captured in zip(recorded_calls, captured_calls):
        recorded.update(captured)

    report["suite_id"] = "property-robustness-v1-approved-sources"
    report["answer_path"] = "approved_sources"
    report["adapter_module"] = "ollama_schema_property_provider"
    report["output_contract_version"] = OUTPUT_CONTRACT_VERSION
    report["cases_file"] = (
        FIXTURES / "cases.json"
    ).relative_to(ROOT).as_posix()
    report["documents_file"] = (
        FIXTURES / "documents.json"
    ).relative_to(ROOT).as_posix()
    report["approvals_file"] = APPROVALS.relative_to(ROOT).as_posix()
    report["approvals_checked_at_start"] = [
        {"document_id": document_id, "version": version}
        for document_id, version in sorted(approved)
    ]

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"answer-robustness-approved-schema-{stamp}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    for case in report["cases"]:
        source_ids = [
            source["document_id"]
            for call in case["provider_calls"]
            for source in call["sources"]
        ]
        print(
            f"{case['case_id']}: "
            f"expected={case['expected_behavior']}; "
            f"actual={case['response']['status']}; "
            f"provider_calls={case['provider_call_count']}; "
            f"sources={source_ids}; "
            f"seconds={case['duration_seconds']}"
        )

    print(f"\nSaved: {path}")
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()