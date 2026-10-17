"""Record two predefined timeout cases without retries or configuration changes."""

import json
import subprocess
import tempfile
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import direct_schema_property_provider as adapter
from answer_approved_property_question import answer_approved_question
from diagnose_entity_predecessor import FIXTURES, APPROVALS
from evaluate_property_answers import ROOT, evaluate, repository_commit
from evaluation_journal import EvaluationJournal
from run_direct_property_robustness import get_json
from run_property_evaluation import OUTPUT, model_metadata
from source_approvals import load_approvals

SELECTED = ["ROBUST-001", "ROBUST-002"]


def memory_snapshot():
    command = (
        "Get-CimInstance Win32_OperatingSystem | "
        "Select-Object TotalVisibleMemorySize,FreePhysicalMemory | "
        "ConvertTo-Json -Compress; "
        "Get-Process llama-server -ErrorAction SilentlyContinue | "
        "Select-Object Id,StartTime,CPU,WorkingSet64,PrivateMemorySize64 | "
        "ConvertTo-Json -Compress; "
        "Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory | "
        "Select-Object AvailableMBytes,CommittedBytes,CommitLimit,"
        "PagesInputPersec,PageReadsPersec | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True, text=True, timeout=30,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit changes before diagnosis")

    version = get_json("http://127.0.0.1:11434/api/version")
    if get_json("http://127.0.0.1:18081/health").get("status") != "ok":
        raise RuntimeError("Direct runner is not ready")

    with (FIXTURES / "cases.json").open(encoding="utf-8-sig") as handle:
        original = json.load(handle)
    selected = [
        case for case in original["cases"]
        if case["case_id"] in SELECTED
    ]
    if [case["case_id"] for case in selected] != SELECTED:
        raise RuntimeError("Expected exactly the predefined two cases")

    configuration = dict(model_metadata())
    if configuration["model"] != adapter.MODEL:
        raise RuntimeError("Model metadata mismatch")
    configuration.update({
        "options": dict(adapter.OPTIONS),
        "endpoint": "http://127.0.0.1:18081/completion",
        "render_endpoint": "http://127.0.0.1:11434/api/generate",
        "cache_prompt": False,
        "socket_timeout_seconds_per_stage": adapter.TIMEOUT_SECONDS,
    })
    configuration.pop("socket_timeout_seconds", None)
    approved = load_approvals(APPROVALS)

    metadata = {
        "experiment": "two-case-existing-runner-timeout-diagnostic",
        "repository_commit": repository_commit(),
        "planned_case_ids": SELECTED,
        "automatic_retries": 0,
        "runner_state": "existing process; no restart or explicit warm-up",
        "ollama_version": version,
        "provider_configuration": configuration,
        "adapter_version": adapter.ADAPTER_VERSION,
        "prompt_version": adapter.PROMPT_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
        "original_cases_file": (
            FIXTURES / "cases.json"
        ).relative_to(ROOT).as_posix(),
        "memory_before": memory_snapshot(),
    }

    def provider(query, context, *, diagnostics=None):
        evidence = json.loads(context)
        for source in evidence["sources"]:
            if (source["document_id"], source["version"]) not in approved:
                raise RuntimeError("Unapproved source reached adapter")
        diagnostics.append({"authorized_evidence": evidence})
        return adapter.provider(query, context, diagnostics=diagnostics)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    journal_path = OUTPUT / f"direct-timeout-diagnostic-{stamp}.jsonl"
    report_path = OUTPUT / f"direct-timeout-diagnostic-{stamp}.json"

    with tempfile.TemporaryDirectory() as directory:
        cases_path = Path(directory) / "cases.json"
        cases_path.write_text(
            json.dumps({"schema_version": "1", "cases": selected}),
            encoding="utf-8",
        )
        with EvaluationJournal(journal_path) as journal:
            journal.append("run_started", **metadata)
            print(f"Journal: {journal_path}", flush=True)

            def started(case_id):
                journal.append("case_started", case_id=case_id)
                print(f"Starting {case_id}...", flush=True)

            def completed(record):
                journal.append("case_completed", record=record)
                print(
                    f"Saved {record['case_id']}: "
                    f"{record['response']['status']}; "
                    f"seconds={record['duration_seconds']}",
                    flush=True,
                )

            try:
                report = evaluate(
                    provider,
                    provider_id="direct-timeout-diagnostic",
                    provider_configuration=configuration,
                    prompt_version=adapter.PROMPT_VERSION,
                    capture_provider_diagnostics=True,
                    answer_function=partial(
                        answer_approved_question, approval_path=APPROVALS
                    ),
                    on_case_start=started,
                    on_case_completed=completed,
                    cases_path=cases_path,
                    document_folder=FIXTURES,
                )
                report.update(metadata)
                report["memory_after"] = memory_snapshot()
                report["journal_file"] = journal_path.relative_to(ROOT).as_posix()
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
    print("No quality scores assigned.")


if __name__ == "__main__":
    main()