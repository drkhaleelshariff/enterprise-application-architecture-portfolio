"""Record robustness cases and the actual authorized evidence supplied."""

import json
import subprocess
from datetime import datetime, timezone

from evaluate_property_answers import ROOT, evaluate
from ollama_property_provider import PROMPT_VERSION, provider
from run_property_evaluation import OUTPUT, model_metadata

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
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
        raise RuntimeError("Commit working-tree changes before evaluation")

    configuration = model_metadata()
    captured_calls = []

    def captured_provider(query, context, *, diagnostics=None):
        call = {
            "question": query,
            "authorized_evidence": json.loads(context),
        }
        captured_calls.append(call)
        return provider(query, context, diagnostics=diagnostics)

    print(
        f"Running robustness cases using {configuration['model']}.",
        flush=True,
    )
    print("Seven cases may invoke the model. Please wait.", flush=True)

    report = evaluate(
        captured_provider,
        provider_id="ollama",
        provider_configuration=configuration,
        prompt_version=PROMPT_VERSION,
        capture_provider_diagnostics=True,
        cases_path=FIXTURES / "cases.json",
        document_folder=FIXTURES,
    )

    # Attach captured inputs in the same sequential order as provider calls.
    recorded_calls = [
        call
        for case in report["cases"]
        for call in case["provider_calls"]
    ]
    if len(recorded_calls) != len(captured_calls):
        raise RuntimeError("Provider input recording count mismatch")

    for recorded, captured in zip(recorded_calls, captured_calls):
        recorded.update(captured)

    report["suite_id"] = "property-robustness-v1"
    report["cases_file"] = (
        FIXTURES / "cases.json"
    ).relative_to(ROOT).as_posix()
    report["documents_file"] = (
        FIXTURES / "documents.json"
    ).relative_to(ROOT).as_posix()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"answer-robustness-{stamp}.json"
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