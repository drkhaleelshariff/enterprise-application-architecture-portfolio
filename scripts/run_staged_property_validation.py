"""Evaluate twelve prepared visitor-permit cases with fresh authorization."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import direct_schema_property_provider as adapter
from answer_staged_property_question import answer_staged_question
from diagnose_direct_timeouts import memory_snapshot
from prepare_staged_property_validation import (
    FIXTURES, APPROVALS, EXPECTED_CASE_IDS,
)
from evaluate_property_answers import ROOT, repository_commit
from evaluation_journal import EvaluationJournal
from run_direct_property_robustness import get_json
from run_property_evaluation import OUTPUT, model_metadata
from staged_property_requests import configuration


def unloaded_models():
    snapshot = get_json("http://127.0.0.1:11434/api/ps")
    if not isinstance(snapshot.get("models"), list):
        raise RuntimeError("Missing Ollama loaded-model list")
    if snapshot["models"]:
        raise RuntimeError("Unload Ollama models before staged generation")
    return snapshot


def run(preparation_path):
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit changes before evaluation")

    preparation_path = Path(preparation_path).resolve()
    raw = preparation_path.read_bytes()
    preparation = json.loads(raw.decode("utf-8-sig"))
    cases_bytes = (FIXTURES / "cases.json").read_bytes()
    cases_document = json.loads(cases_bytes.decode("utf-8-sig"))
    cases = cases_document["cases"]

    if (
        preparation.get("schema_version") != "1"
        or preparation.get("experiment")
        != "staged-property-validation-preparation"
        or preparation.get("suite_id")
        != "staged-visitor-permit-validation-v1"
        or preparation.get("execution_status") != "completed"
        or preparation.get("generation_performed") is not False
    ):
        raise ValueError("Incomplete or invalid preparation")
    if preparation["configuration"] != configuration():
        raise ValueError("Preparation configuration differs")
    if preparation["cases_file_sha256"] != hashlib.sha256(
        cases_bytes
    ).hexdigest():
        raise ValueError("Case definitions changed")
    if (
        cases_document.get("schema_version") != "1"
        or [case["case_id"] for case in cases] != EXPECTED_CASE_IDS
        or [entry["case"] for entry in preparation["cases"]] != cases
    ):
        raise ValueError("Prepared cases differ from the validation suite")

    expected_cases_file = (
        FIXTURES / "cases.json"
    ).relative_to(ROOT).as_posix()
    if preparation.get("cases_file") != expected_cases_file:
        raise ValueError("Preparation refers to a different cases file")

    current_fixture_hashes = {
        name: hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
        for name in (
            "plan.md", "cases.json", "documents.json",
            "source_approvals.json",
        )
    }
    if preparation.get("fixture_sha256") != current_fixture_hashes:
        raise ValueError("Validation fixtures changed after preparation")

    model = model_metadata()
    if (
        model["model"] != preparation["model"]
        or model["digest"] != preparation["model_digest"]
    ):
        raise ValueError("Installed model metadata differs from preparation")
    version = get_json("http://127.0.0.1:11434/api/version")
    if version != preparation["ollama_version"]:
        raise ValueError("Ollama version changed after preparation")
    residency = unloaded_models()
    health = get_json("http://127.0.0.1:18081/health")
    if health.get("status") != "ok":
        raise RuntimeError("Direct runner is not ready")

    report = {
        "schema_version": "1",
        "experiment": "staged-property-validation-generation",
        "suite_id": "staged-visitor-permit-validation-v1",
        "fixture_sha256": current_fixture_hashes,
        "repository_commit": repository_commit(),
        "preparation_file": str(preparation_path),
        "preparation_sha256": hashlib.sha256(raw).hexdigest(),
        "model": preparation["model"],
        "model_digest": preparation["model_digest"],
        "configuration": configuration(),
        "ollama_version": version,
        "ollama_models_before": residency,
        "direct_runner_health": health,
        "runner_configuration": "External; verify separately captured log",
        "completion_timeout_seconds": adapter.TIMEOUT_SECONDS,
        "automatic_retries": 0,
        "review_status": "not_reviewed",
        "memory_before": memory_snapshot(),
        "cases": [],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    report_path = OUTPUT / f"answer-validation-staged-{stamp}.json"
    journal_path = OUTPUT / f"answer-validation-staged-{stamp}.jsonl"

    with EvaluationJournal(journal_path) as journal:
        journal.append(
            "run_started",
            metadata={k: v for k, v in report.items() if k != "cases"},
        )
        print(f"Journal: {journal_path}", flush=True)
        try:
            for entry in preparation["cases"]:
                case = entry["case"]
                record = dict(case)
                record.update({
                    "provider_call_count": 0,
                    "diagnostics": [],
                    "review": {"decision": "not_assessed", "explanation": ""},
                    "ollama_models_before_case": unloaded_models(),
                })
                journal.append("case_started", case_id=case["case_id"])
                print(f"Starting {case['case_id']}...", flush=True)

                def completion(payload, diagnostics):
                    record["provider_call_count"] += 1
                    # Called only after the staged boundary validates current context.
                    record["authorized_evidence"] = json.loads(
                        entry["prepared"]["context_result"]["context"]
                    )
                    return adapter.post_json(
                        18081, "/completion", payload,
                        "completion", diagnostics,
                    )

                started = perf_counter()
                record["response"] = answer_staged_question(
                    entry["prepared"],
                    case["identity_id"],
                    case["question"],
                    document_folder=FIXTURES,
                    approval_path=APPROVALS,
                    diagnostics=record["diagnostics"],
                    completion_function=completion,
                )
                record["duration_seconds"] = round(
                    perf_counter() - started, 6
                )
                report["cases"].append(record)
                # Save the outcome before the post-case residency check.
                journal.append("case_completed", record=record)
                print(
                    f"Saved {case['case_id']}: "
                    f"actual={record['response']['status']}; "
                    f"calls={record['provider_call_count']}; "
                    f"seconds={record['duration_seconds']}",
                    flush=True,
                )
                journal.append(
                    "residency_checked",
                    case_id=case["case_id"],
                    ollama_models=unloaded_models(),
                )

            report["execution_status"] = "completed"
            report["case_count"] = len(report["cases"])
            report["memory_after"] = memory_snapshot()
            report["journal_file"] = journal_path.relative_to(ROOT).as_posix()
            report["recorded_at"] = datetime.now(timezone.utc).isoformat()
            with report_path.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            journal.append(
                "run_completed",
                report_file=report_path.relative_to(ROOT).as_posix(),
                memory_after=report["memory_after"],
            )
        except BaseException as exc:
            journal.append(
                "run_interrupted",
                error_type=type(exc).__name__,
                message=str(exc),
            )
            raise

    print(f"Saved: {report_path}")
    print("Review required. No quality scores assigned.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("preparation")
    args = parser.parse_args()
    run(args.preparation)


if __name__ == "__main__":
    main()