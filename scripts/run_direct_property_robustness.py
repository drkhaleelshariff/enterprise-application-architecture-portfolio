"""Record unchanged robustness cases through the direct no-reuse adapter."""

import json
import subprocess
from datetime import datetime, timezone
from functools import partial
from urllib.request import urlopen
from evaluation_journal import EvaluationJournal
from evaluate_property_answers import repository_commit

import direct_schema_property_provider as adapter
from answer_approved_property_question import answer_approved_question
from diagnose_entity_predecessor import FIXTURES, APPROVALS
from evaluate_property_answers import ROOT, evaluate
from run_property_evaluation import OUTPUT, model_metadata
from source_approvals import load_approvals


def get_json(url):
    with urlopen(url, timeout=10) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object from service")
    return result


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit working-tree changes before evaluation")

    # Preflight checks do not request answer generation.
    ollama_version = get_json("http://127.0.0.1:11434/api/version")
    runner_health = get_json("http://127.0.0.1:18081/health")
    if runner_health.get("status") != "ok":
        raise RuntimeError("Direct runner is not ready")

    configuration = dict(model_metadata())
    if configuration["model"] != adapter.MODEL:
        raise RuntimeError("Metadata model differs from adapter model")
    configuration.update({
        "options": dict(adapter.OPTIONS),
        "endpoint": "http://127.0.0.1:18081/completion",
        "render_endpoint": "http://127.0.0.1:11434/api/generate",
        "render_only": True,
        "cache_prompt": False,
        "socket_timeout_seconds_per_stage": adapter.TIMEOUT_SECONDS,
    })
    # Avoid presenting the old single-stage timeout as a total deadline.
    configuration.pop("socket_timeout_seconds", None)

    approved = load_approvals(APPROVALS)
    captured_calls = []

    def captured_provider(query, context, *, diagnostics=None):
        evidence = json.loads(context)
        for source in evidence["sources"]:
            if (source["document_id"], source["version"]) not in approved:
                raise RuntimeError("Unapproved source reached provider")

        captured_calls.append({
            "question": query,
            "authorized_evidence": evidence,
            "requested_schema": adapter.response_schema(evidence),
        })
        return adapter.provider(query, context, diagnostics=diagnostics)

    print(
        "Running unchanged robustness cases through the direct adapter.",
        flush=True,
    )
    print(
        "Seven cases may generate answers; no automatic retries.",
        flush=True,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    journal_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    journal_path = OUTPUT / (
        f"answer-robustness-direct-no-reuse-{journal_stamp}.jsonl"
    )
    captured_offset = 0

    with EvaluationJournal(journal_path) as journal:
        journal.append(
            "run_started",
            repository_commit=repository_commit(),
            provider_configuration=configuration,
            prompt_version=adapter.PROMPT_VERSION,
            adapter_version=adapter.ADAPTER_VERSION,
            output_contract_version=adapter.OUTPUT_CONTRACT_VERSION,
            ollama_version=ollama_version,
            runner_health=runner_health,
            cases_file=(FIXTURES / "cases.json").relative_to(ROOT).as_posix(),
            documents_file=(
                FIXTURES / "documents.json"
            ).relative_to(ROOT).as_posix(),
            approvals_file=APPROVALS.relative_to(ROOT).as_posix(),
            approved_sources=[
                {"document_id": doc, "version": version}
                for doc, version in sorted(approved)
            ],
            automatic_retries=0,
        )
        print(f"Journal: {journal_path}", flush=True)

        def case_started(case_id):
            journal.append("case_started", case_id=case_id)
            print(f"Starting {case_id}...", flush=True)

        def case_completed(record):
            nonlocal captured_offset
            calls = record["provider_calls"]
            captured = captured_calls[
                captured_offset:captured_offset + len(calls)
            ]
            if len(captured) != len(calls):
                raise RuntimeError("Per-case provider recording mismatch")
            for recorded, extra in zip(calls, captured):
                recorded.update(extra)
            captured_offset += len(calls)

            journal.append("case_completed", record=record)
            print(
                f"Saved {record['case_id']}: "
                f"actual={record['response']['status']}; "
                f"seconds={record['duration_seconds']}",
                flush=True,
            )

        try:
            report = evaluate(
                captured_provider,
                provider_id="direct-llama-server-with-ollama-rendering",
                provider_configuration=configuration,
                prompt_version=adapter.PROMPT_VERSION,
                capture_provider_diagnostics=True,
                answer_function=partial(
                    answer_approved_question,
                    approval_path=APPROVALS,
                ),
                on_case_start=case_started,
                on_case_completed=case_completed,
                cases_path=FIXTURES / "cases.json",
                document_folder=FIXTURES,
            )
            if captured_offset != len(captured_calls):
                raise RuntimeError("Unmatched provider calls remain")
        except BaseException as exc:
            journal.append(
                "run_interrupted",
                error_type=type(exc).__name__,
                message=str(exc),
            )
            raise
        else:
            journal.append(
                "evaluation_finished",
                case_count=report["case_count"],
            )

    report["journal_file"] = journal_path.relative_to(ROOT).as_posix()

    report.update({
        "suite_id": "property-robustness-v1-approved-sources",
        "answer_path": "approved_sources",
        "adapter_module": adapter.__name__,
        "adapter_version": adapter.ADAPTER_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
        "automatic_retries": 0,
        "ollama_version_at_start": ollama_version,
        "direct_runner_health_at_start": runner_health,
        "cases_file": (FIXTURES / "cases.json").relative_to(ROOT).as_posix(),
        "documents_file": (
            FIXTURES / "documents.json"
        ).relative_to(ROOT).as_posix(),
        "approvals_file": APPROVALS.relative_to(ROOT).as_posix(),
        "approvals_checked_at_start": [
            {"document_id": doc, "version": version}
            for doc, version in sorted(approved)
        ],
        "runner_launch_configuration": (
            "Externally managed; verify against separately captured runner log"
        ),
    })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"answer-robustness-direct-no-reuse-{stamp}.json"
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
    print(f"Saved: {path}")
    print("Review required. No quality scores assigned.")


if __name__ == "__main__":
    main()
