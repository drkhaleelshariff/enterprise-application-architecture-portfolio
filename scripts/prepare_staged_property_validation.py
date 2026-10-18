"""Prepare twelve visitor-permit validation cases without answer generation."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone

import direct_schema_property_provider as adapter
from build_approved_context import build_approved_context
from evaluate_property_answers import ROOT, repository_commit
from evaluation_journal import EvaluationJournal
from run_direct_property_robustness import get_json
from run_property_evaluation import OUTPUT, model_metadata
from staged_property_requests import configuration, prepare_request

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "staged_validation_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"
EXPECTED_CASE_IDS = [f"STVAL-{number:03d}" for number in range(1, 13)]

def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit changes before preparation")

    cases_path = FIXTURES / "cases.json"
    cases_bytes = cases_path.read_bytes()
    cases_document = json.loads(cases_bytes.decode("utf-8-sig"))
    if cases_document.get("schema_version") != "1":
        raise ValueError("Unsupported case schema")
    cases = cases_document["cases"]
    if [case["case_id"] for case in cases] != EXPECTED_CASE_IDS:
        raise ValueError("Expected STVAL-001 through STVAL-012 in plan order")

    model = dict(model_metadata())
    if model["model"] != adapter.MODEL:
        raise RuntimeError("Model metadata mismatch")

    report = {
        "schema_version": "1",
        "experiment": "staged-property-validation-preparation",
        "suite_id": "staged-visitor-permit-validation-v1",
        "fixture_sha256": {
            name: hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
            for name in (
                "plan.md", "cases.json", "documents.json",
                "source_approvals.json",
            )
        },
        "repository_commit": repository_commit(),
        "ollama_version": get_json("http://127.0.0.1:11434/api/version"),
        "model": adapter.MODEL,
        "model_digest": model["digest"],
        "configuration": configuration(),
        "cases_file": cases_path.relative_to(ROOT).as_posix(),
        "cases_file_sha256": hashlib.sha256(cases_bytes).hexdigest(),
        "generation_performed": False,
        "review_status": "not_reviewed",
        "cases": [],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"staged-validation-preparation-{stamp}.json"
    journal_path = OUTPUT / f"staged-validation-preparation-{stamp}.jsonl"

    with EvaluationJournal(journal_path) as journal:
        journal.append(
            "preparation_started",
            metadata={k: v for k, v in report.items() if k != "cases"},
        )
        try:
            for case in cases:
                print(f"Preparing {case['case_id']}...", flush=True)
                journal.append(
                    "case_preparation_started", case_id=case["case_id"]
                )
                diagnostics = []

                def render(payload):
                    return adapter.post_json(
                        11434, "/api/generate", payload,
                        "render", diagnostics,
                    )

                context = build_approved_context(
                    case["identity_id"],
                    case["question"],
                    document_folder=FIXTURES,
                    approval_path=APPROVALS,
                )
                prepared = prepare_request(
                    case["identity_id"], case["question"], context, render
                )
                record = {
                    "case": case,
                    "prepared": prepared,
                    "render_diagnostics": diagnostics,
                }
                report["cases"].append(record)
                journal.append("case_prepared", record=record)
                print(
                    f"Saved preparation {case['case_id']}: "
                    f"context={context['context_status']}; "
                    f"rendered={prepared['completion_request'] is not None}",
                    flush=True,
                )

            report["execution_status"] = "completed"
            report["recorded_at"] = datetime.now(timezone.utc).isoformat()
            report["journal_file"] = journal_path.relative_to(ROOT).as_posix()
            with path.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            journal.append(
                "preparation_completed",
                preparation_file=path.relative_to(ROOT).as_posix(),
                case_count=len(report["cases"]),
            )
        except BaseException as exc:
            journal.append(
                "preparation_interrupted",
                error_type=type(exc).__name__,
                message=str(exc),
            )
            raise

    print(f"Saved: {path}")
    print("Preparation only. No answers generated.")


if __name__ == "__main__":
    main()