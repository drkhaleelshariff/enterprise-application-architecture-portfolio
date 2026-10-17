"""Replay two captured requests without loading Ollama's rendering model."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from time import perf_counter

import direct_schema_property_provider as adapter
from answer_approved_property_question import answer_approved_question
from answer_property_question import ProviderUnavailable
from diagnose_direct_timeouts import memory_snapshot
from diagnose_entity_predecessor import FIXTURES, APPROVALS
from evaluate_property_answers import ROOT, repository_commit
from evaluation_journal import EvaluationJournal
from run_direct_property_robustness import get_json
from run_property_evaluation import OUTPUT

SOURCE = (
    "projects/05-permission-aware-rag/evidence/"
    "direct-timeout-diagnostic-20261017T171030670278Z.json"
)


def unloaded_models():
    snapshot = get_json("http://127.0.0.1:11434/api/ps")
    if not isinstance(snapshot.get("models"), list):
        raise RuntimeError("Missing Ollama loaded-model list")
    if snapshot["models"]:
        raise RuntimeError("Ollama has a loaded model; replay stopped")
    return snapshot


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit changes before replay")

    source_bytes = (ROOT / SOURCE).read_bytes()
    source = json.loads(source_bytes)
    if [c["case_id"] for c in source["cases"]] != [
        "ROBUST-001", "ROBUST-002"
    ]:
        raise RuntimeError("Unexpected source cases")
    if get_json("http://127.0.0.1:18081/health").get("status") != "ok":
        raise RuntimeError("Direct runner is not ready")

    report = {
        "experiment": "captured-two-case-replay-without-live-rendering",
        "repository_commit": repository_commit(),
        "source_file": SOURCE,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "ollama_version": get_json("http://127.0.0.1:11434/api/version"),
        "ollama_models_before": unloaded_models(),
        "memory_before": memory_snapshot(),
        "runner_state": "existing process; no explicit restart or warm-up",
        "automatic_retries": 0,
        "completion_timeout_seconds": adapter.TIMEOUT_SECONDS,
        "review_status": "not_reviewed",
        "cases": [],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    journal_path = OUTPUT / f"direct-replay-{stamp}.jsonl"
    report_path = OUTPUT / f"direct-replay-{stamp}.json"

    with EvaluationJournal(journal_path) as journal:
        journal.append(
            "run_started",
            metadata={k: v for k, v in report.items() if k != "cases"},
        )
        print(f"Journal: {journal_path}", flush=True)
        try:
            for case in source["cases"]:
                entries = [
                    entry
                    for call in case["provider_calls"]
                    for entry in call["diagnostics"]
                    if entry.get("stage") == "completion"
                    and "request_body_utf8" in entry
                ]
                if len(entries) != 1:
                    raise RuntimeError("Expected one captured completion request")
                entry = entries[0]
                original_body = entry["request_body_utf8"].encode("utf-8")
                if hashlib.sha256(original_body).hexdigest() != entry[
                    "request_body_sha256"
                ]:
                    raise RuntimeError("Source request hash mismatch")

                payload = json.loads(original_body)
                serialized = json.dumps(
                    payload, ensure_ascii=False
                ).encode("utf-8")
                if serialized != original_body:
                    raise RuntimeError("Reserialized request differs")
                if payload.get("cache_prompt") is not False:
                    raise RuntimeError("Expected prefix reuse disabled")

                record = {
                    "case_id": case["case_id"],
                    "expected_behavior": case["expected_behavior"],
                    "source_request_sha256": entry["request_body_sha256"],
                    "ollama_models_before_case": unloaded_models(),
                    "diagnostics": [],
                }
                journal.append("case_started", case_id=case["case_id"])
                print(f"Starting {case['case_id']}...", flush=True)

                def replay_provider(query, context):
                    if query != case["question"]:
                        raise RuntimeError("Question changed")
                    evidence = json.loads(context)
                    source_evidence = case["provider_calls"][0]["diagnostics"][0][
                        "authorized_evidence"
                    ]
                    if evidence != source_evidence:
                        raise RuntimeError("Authorized evidence changed")
                    if adapter.response_schema(evidence) != payload["json_schema"]:
                        raise RuntimeError("Response schema changed")

                    result = adapter.post_json(
                        18081, "/completion", payload,
                        "completion", record["diagnostics"],
                    )
                    record["runner_response"] = result
                    content = result.get("content")
                    if (
                        result.get("stop") is not True
                        or result.get("stop_type") not in {"eos", "word"}
                        or result.get("truncated") is not False
                        or result.get("stopped_limit") is True
                        or not isinstance(content, str)
                    ):
                        return {}
                    try:
                        return json.loads(
                            content, object_pairs_hook=adapter.unique_object
                        )
                    except (ValueError, RecursionError):
                        return {}

                started = perf_counter()
                record["response"] = answer_approved_question(
                    case["identity_id"],
                    case["question"],
                    replay_provider,
                    document_folder=FIXTURES,
                    approval_path=APPROVALS,
                )
                record["duration_seconds"] = round(
                    perf_counter() - started, 6
                )
                record["ollama_models_after_case"] = unloaded_models()
                report["cases"].append(record)
                journal.append("case_completed", record=record)
                print(json.dumps(record["response"], indent=2), flush=True)

            report["memory_after"] = memory_snapshot()
            report["execution_status"] = "completed"
        except BaseException as exc:
            report["execution_status"] = "interrupted"
            journal.append(
                "run_interrupted",
                error_type=type(exc).__name__,
                message=str(exc),
            )
            raise
        else:
            report["journal_file"] = journal_path.relative_to(ROOT).as_posix()
            with report_path.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            journal.append(
                "run_completed",
                report_file=report_path.relative_to(ROOT).as_posix(),
                memory_after=report["memory_after"],
            )
            print(f"Saved: {report_path}", flush=True)


if __name__ == "__main__":
    main()