"""Save an Ollama evaluation run for later human review."""

import json
import subprocess
from datetime import datetime, timezone
from http.client import HTTPConnection

from evaluate_property_answers import ROOT, evaluate
from ollama_property_provider import MODEL, OPTIONS, PROMPT_VERSION, provider

OUTPUT = (
    ROOT / "projects" / "05-permission-aware-rag" / "evidence"
)


def model_metadata():
    connection = HTTPConnection("127.0.0.1", 11434, timeout=10)
    try:
        connection.request("GET", "/api/tags")
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError("Cannot read local model metadata")
        document = json.loads(response.read())
    finally:
        connection.close()

    for model in document["models"]:
        if model["name"] == MODEL:
            return {
                "model": MODEL,
                "digest": model["digest"],
                "options": OPTIONS.copy(),
                "endpoint": "http://127.0.0.1:11434/api/generate",
                "socket_timeout_seconds": 180,
            }

    raise RuntimeError(f"Required model is unavailable: {MODEL}")


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError(
            "Commit or resolve working-tree changes before evaluation"
        )

    configuration = model_metadata()

    print(f"Evaluating eight cases using {MODEL}.", flush=True)
    print("Six cases may invoke the model. Please wait.", flush=True)

    report = evaluate(
        provider,
        provider_id="ollama",
        provider_configuration=configuration,
        prompt_version=PROMPT_VERSION,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"answer-evaluation-{stamp}.json"

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
    print("Review status: not_reviewed. No quality pass rate assigned.")


if __name__ == "__main__":
    main()