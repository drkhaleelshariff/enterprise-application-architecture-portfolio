"""Record five identical entity-mismatch requests without retries."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPException
from time import perf_counter

import ollama_property_provider as baseline
import ollama_schema_property_provider as adapter
from answer_approved_property_question import answer_approved_question
from evaluate_property_answers import ROOT, repository_commit
from run_property_evaluation import OUTPUT, model_metadata
from source_approvals import load_approvals

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"
QUESTION = (
    "What is the target acknowledgement time for South "
    "replacement access card requests?"
)
REPETITIONS = 5


def service_version():
    connection = HTTPConnection("127.0.0.1", 11434, timeout=10)
    try:
        connection.request("GET", "/api/version")
        response = connection.getresponse()
        raw = response.read(65537)
        if response.status != 200 or len(raw) > 65536:
            return {"status": "unavailable"}

        result = json.loads(raw)
        if not isinstance(result, dict):
            return {"status": "invalid_response"}

        return {"status": "recorded", "response": result}
    except (OSError, HTTPException, ValueError) as exc:
        return {
            "status": "unavailable",
            "error_type": type(exc).__name__,
        }
    finally:
        connection.close()


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

    for name in (
        "MODEL", "THINK", "PROMPT_VERSION", "OPTIONS", "SYSTEM_PROMPT"
    ):
        if getattr(baseline, name) != getattr(adapter, name):
            raise RuntimeError(f"Adapter configuration differs: {name}")

    approved = load_approvals(APPROVALS)
    report = {
        "schema_version": "1",
        "experiment": "entity-mismatch-five-identical-requests",
        "repository_commit": repository_commit(),
        "provider_configuration": model_metadata(),
        "service_version_at_start": service_version(),
        "adapter_module": adapter.__name__,
        "prompt_version": adapter.PROMPT_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
        "identity_id": "USR-001",
        "question": QUESTION,
        "expected_behavior": "abstain",
        "required_citations": [],
        "planned_repetitions": REPETITIONS,
        "automatic_retries": 0,
        "documents_file": (
            FIXTURES / "documents.json"
        ).relative_to(ROOT).as_posix(),
        "approvals_file": APPROVALS.relative_to(ROOT).as_posix(),
        "approvals_checked_at_start": [
            {"document_id": document_id, "version": version}
            for document_id, version in sorted(approved)
        ],
        "review_status": "not_reviewed",
        "attempts": [],
    }

    for attempt_number in range(1, REPETITIONS + 1):
        calls = []

        def captured_provider(query, context):
            evidence = json.loads(context)
            sources = evidence["sources"]

            if [
                source["citation"] for source in sources
            ] != ["DOC-N-ACCESS-001:v1"]:
                raise RuntimeError("Unexpected evidence")

            for source in sources:
                key = (source["document_id"], source["version"])
                if key not in approved:
                    raise RuntimeError("Unapproved source reached provider")

            call = {
                "question": query,
                "authorized_evidence": evidence,
                "diagnostics": [],
            }
            calls.append(call)

            return adapter.provider(
                query,
                context,
                diagnostics=call["diagnostics"],
            )

        print(
            f"Running attempt {attempt_number}/{REPETITIONS}...",
            flush=True,
        )
        started = perf_counter()

        response = answer_approved_question(
            "USR-001",
            QUESTION,
            captured_provider,
            document_folder=FIXTURES,
            approval_path=APPROVALS,
        )

        report["attempts"].append({
            "attempt": attempt_number,
            "provider_call_count": len(calls),
            "provider_calls": calls,
            "response": response,
            "duration_seconds": round(perf_counter() - started, 6),
        })
        print(
            json.dumps(response, ensure_ascii=False, indent=2),
            flush=True,
        )

    # Check request capture after all five outcomes have been collected.
    bodies = []
    capture_complete = True
    hashes_verified = True

    for attempt in report["attempts"]:
        request_entries = [
            entry
            for call in attempt["provider_calls"]
            for entry in call["diagnostics"]
            if "request_body_utf8" in entry
        ]
        if (
            attempt["provider_call_count"] != 1
            or len(request_entries) != 1
        ):
            capture_complete = False
            continue

        entry = request_entries[0]
        body = entry["request_body_utf8"]
        actual_hash = hashlib.sha256(
            body.encode("utf-8")
        ).hexdigest()
        if actual_hash != entry.get("request_body_sha256"):
            hashes_verified = False
        bodies.append(body)

    report["request_comparison"] = {
        "capture_complete": capture_complete,
        "captured_request_count": len(bodies),
        "recorded_hashes_verified": hashes_verified,
        "all_request_bodies_identical": (
            capture_complete
            and len(bodies) == REPETITIONS
            and len(set(bodies)) == 1
        ),
    }

    report["service_version_at_end"] = service_version()
    report["recorded_at"] = datetime.now(timezone.utc).isoformat()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"entity-repeatability-diagnostic-{stamp}.json"

    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Saved: {path}")
    print(json.dumps(report["request_comparison"], indent=2))
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()