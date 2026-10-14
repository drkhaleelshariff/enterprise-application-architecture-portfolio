"""Record new validation cases using the frozen provider configuration."""

import json
import subprocess
from datetime import datetime, timezone

from evaluate_property_answers import ROOT, evaluate
from ollama_property_provider import PROMPT_VERSION, provider
from run_property_evaluation import OUTPUT, model_metadata

CASES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "answer_validation_cases.json"
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
        raise RuntimeError("Commit working-tree changes before validation")

    configuration = model_metadata()
    print(
        f"Running validation cases using {configuration['model']}.",
        flush=True,
    )
    print("Seven cases may invoke the model. Please wait.", flush=True)

    report = evaluate(
        provider,
        provider_id="ollama",
        provider_configuration=configuration,
        prompt_version=PROMPT_VERSION,
        capture_provider_diagnostics=True,
        cases_path=CASES,
    )
    report["suite_id"] = "property-validation-v1"
    report["cases_file"] = CASES.relative_to(ROOT).as_posix()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"answer-validation-{stamp}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    for case in report["cases"]:
        print(
            f"{case['case_id']}: "
            f"expected={case['expected_behavior']}; "
            f"actual={case['response']['status']}; "
            f"provider_calls={case['provider_call_count']}; "
            f"seconds={case['duration_seconds']}"
        )

    print(f"\nSaved: {path}")
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()