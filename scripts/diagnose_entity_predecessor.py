"""Compare isolated, North-preceded and South-preceded mismatch requests."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from http.client import HTTPConnection
from time import perf_counter

import ollama_property_provider as baseline
import ollama_schema_property_provider as adapter
from answer_approved_property_question import answer_approved_question
from diagnose_entity_repeatability import service_version
from evaluate_property_answers import ROOT, repository_commit
from run_property_evaluation import OUTPUT, model_metadata
from source_approvals import load_approvals

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"

PLAN = [
    ("A", ["ROBUST-003"]),
    ("N", ["ROBUST-001", "ROBUST-003"]),
    ("S", ["ROBUST-002", "ROBUST-003"]),
    ("S", ["ROBUST-002", "ROBUST-003"]),
    ("N", ["ROBUST-001", "ROBUST-003"]),
    ("A", ["ROBUST-003"]),
]


def loaded_models():
    connection = HTTPConnection("127.0.0.1", 11434, timeout=10)
    try:
        connection.request("GET", "/api/ps")
        response = connection.getresponse()
        raw = response.read(1_048_577)
        if response.status != 200 or len(raw) > 1_048_576:
            raise RuntimeError("Cannot verify loaded models")
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("Invalid loaded-model response")
        if not isinstance(result.get("models"), list):
            raise ValueError("Missing loaded-model list")
        return result
    finally:
        connection.close()


def run_case(case, approved):
    calls = []

    def captured_provider(query, context):
        evidence = json.loads(context)
        expected = (
            "DOC-S-ACCESS-001:v1"
            if case["case_id"] == "ROBUST-002"
            else "DOC-N-ACCESS-001:v1"
        )
        if [
            source["citation"] for source in evidence["sources"]
        ] != [expected]:
            raise RuntimeError("Unexpected evidence")

        for source in evidence["sources"]:
            if (source["document_id"], source["version"]) not in approved:
                raise RuntimeError("Unapproved source reached provider")

        call = {
            "question": query,
            "authorized_evidence": evidence,
            "diagnostics": [],
        }
        calls.append(call)
        return adapter.provider(
            query, context, diagnostics=call["diagnostics"]
        )

    started = perf_counter()
    response = answer_approved_question(
        case["identity_id"],
        case["question"],
        captured_provider,
        document_folder=FIXTURES,
        approval_path=APPROVALS,
    )
    return {
        "case": case,
        "provider_call_count": len(calls),
        "provider_calls": calls,
        "response": response,
        "duration_seconds": round(perf_counter() - started, 6),
    }


def target_comparison(report):
    bodies = []
    hashes_verified = True
    target_count = 0

    for sequence in report["sequences"]:
        for record in sequence["requests"]:
            if record["case"]["case_id"] != "ROBUST-003":
                continue
            target_count += 1
            entries = [
                entry
                for call in record["provider_calls"]
                for entry in call["diagnostics"]
                if "request_body_utf8" in entry
            ]
            if record["provider_call_count"] != 1 or len(entries) != 1:
                continue
            entry = entries[0]
            body = entry["request_body_utf8"]
            calculated = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if calculated != entry.get("request_body_sha256"):
                hashes_verified = False
            bodies.append(body)

    return {
        "planned_target_count": len(PLAN),
        "recorded_target_count": target_count,
        "captured_target_request_count": len(bodies),
        "recorded_hashes_verified": hashes_verified,
        "all_target_request_bodies_identical": (
            target_count == len(PLAN)
            and len(bodies) == len(PLAN)
            and len(set(bodies)) == 1
        ),
    }


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit working-tree changes before diagnosis")

    for name in (
        "MODEL", "THINK", "PROMPT_VERSION", "OPTIONS", "SYSTEM_PROMPT"
    ):
        if getattr(baseline, name) != getattr(adapter, name):
            raise RuntimeError(f"Adapter configuration differs: {name}")

    # Process-local changes; model_metadata shares baseline's options.
    baseline.OPTIONS["num_gpu"] = 0
    adapter.OPTIONS["num_gpu"] = 0

    with (FIXTURES / "cases.json").open(encoding="utf-8-sig") as handle:
        cases = {
            case["case_id"]: case
            for case in json.load(handle)["cases"]
        }
    approved = load_approvals(APPROVALS)

    report = {
        "schema_version": "1",
        "experiment": "entity-predecessor-anssna",
        "repository_commit": repository_commit(),
        "provider_configuration": model_metadata(),
        "service_version_at_start": service_version(),
        "adapter_module": adapter.__name__,
        "prompt_version": adapter.PROMPT_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
        "planned_sequences": [
            {"condition": label, "case_ids": ids}
            for label, ids in PLAN
        ],
        "automatic_retries": 0,
        "cases_file": (FIXTURES / "cases.json").relative_to(ROOT).as_posix(),
        "documents_file": (
            FIXTURES / "documents.json"
        ).relative_to(ROOT).as_posix(),
        "approvals_file": APPROVALS.relative_to(ROOT).as_posix(),
        "approvals_checked_at_start": [
            {"document_id": doc, "version": version}
            for doc, version in sorted(approved)
        ],
        "review_status": "not_reviewed",
        "execution_status": "running",
        "sequences": [],
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"entity-predecessor-diagnostic-{stamp}.json"

    try:
        for number, (label, case_ids) in enumerate(PLAN, start=1):
            sequence = {
                "sequence": number,
                "condition": label,
                "requests": [],
            }
            report["sequences"].append(sequence)
            print(
                f"Sequence {number}/{len(PLAN)}: {label}",
                flush=True,
            )

            stopped = subprocess.run(
                ["ollama", "stop", adapter.MODEL],
                capture_output=True, text=True, timeout=60,
            )
            sequence["unload"] = {
                "returncode": stopped.returncode,
                "stdout": stopped.stdout,
                "stderr": stopped.stderr,
            }
            if stopped.returncode != 0:
                raise RuntimeError("Model unload failed")

            snapshot = loaded_models()
            sequence["loaded_models_after_unload"] = snapshot
            if any(
                model.get("name") == adapter.MODEL
                or model.get("model") == adapter.MODEL
                for model in snapshot["models"]
            ):
                raise RuntimeError("Qwen remains loaded after unload")

            for case_id in case_ids:
                print(f"Running {case_id}...", flush=True)
                record = run_case(cases[case_id], approved)
                sequence["requests"].append(record)
                print(
                    json.dumps(record["response"], indent=2),
                    flush=True,
                )

        report["execution_status"] = "completed"
    except Exception as exc:
        report["execution_status"] = "interrupted"
        report["experiment_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        raise
    finally:
        report["target_request_comparison"] = target_comparison(report)
        report["service_version_at_end"] = service_version()
        report["recorded_at"] = datetime.now(timezone.utc).isoformat()
        with path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Saved: {path}", flush=True)
        print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()