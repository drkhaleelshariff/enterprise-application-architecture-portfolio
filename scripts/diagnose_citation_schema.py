"""Compare JSON mode and citation-schema mode on ROBUST-006."""

import json
import subprocess
from datetime import datetime, timezone
from time import perf_counter

import ollama_property_provider as baseline
import ollama_schema_property_provider as experimental
from answer_approved_property_question import answer_approved_question
from evaluate_property_answers import ROOT, repository_commit
from run_property_evaluation import OUTPUT, model_metadata
from source_approvals import load_approvals

FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"


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

    # Only the requested output format should differ between adapters.
    for name in (
        "MODEL", "THINK", "PROMPT_VERSION", "OPTIONS", "SYSTEM_PROMPT"
    ):
        if getattr(baseline, name) != getattr(experimental, name):
            raise RuntimeError(f"Adapter configuration differs: {name}")

    with (FIXTURES / "cases.json").open(
        encoding="utf-8-sig"
    ) as handle:
        cases = json.load(handle)["cases"]

    selected = [
        case for case in cases
        if case["case_id"] == "ROBUST-006"
    ]
    if len(selected) != 1:
        raise RuntimeError("Expected exactly one ROBUST-006 case")
    case = selected[0]

    approved = load_approvals(APPROVALS)
    report = {
        "schema_version": "1",
        "experiment": "citation-json-versus-schema",
        "repository_commit": repository_commit(),
        "provider_configuration": model_metadata(),
        "prompt_version": baseline.PROMPT_VERSION,
        "case": case,
        "documents_file": (
            FIXTURES / "documents.json"
        ).relative_to(ROOT).as_posix(),
        "approvals_file": APPROVALS.relative_to(ROOT).as_posix(),
        "approvals_checked_at_start": [
            {"document_id": document_id, "version": version}
            for document_id, version in sorted(approved)
        ],
        "review_status": "not_reviewed",
        "conditions": [],
    }

    first_context = None

    for condition, adapter in (
        ("json_mode", baseline),
        ("citation_schema", experimental),
    ):
        calls = []

        def captured_provider(query, context):
            nonlocal first_context
            evidence = json.loads(context)

            for source in evidence["sources"]:
                key = (source["document_id"], source["version"])
                if key not in approved:
                    raise RuntimeError("Unapproved source reached provider")

            if first_context is None:
                first_context = evidence
            elif evidence != first_context:
                raise RuntimeError("Comparison contexts differ")

            requested_format = (
                experimental.response_schema(evidence)
                if condition == "citation_schema"
                else "json"
            )
            call = {
                "question": query,
                "authorized_evidence": evidence,
                "requested_format": requested_format,
                "diagnostics": [],
            }
            calls.append(call)

            return adapter.provider(
                query,
                context,
                diagnostics=call["diagnostics"],
            )

        print(f"Running {condition}...", flush=True)
        started = perf_counter()

        response = answer_approved_question(
            case["identity_id"],
            case["question"],
            captured_provider,
            document_folder=FIXTURES,
            approval_path=APPROVALS,
        )

        report["conditions"].append({
            "condition": condition,
            "adapter_module": adapter.__name__,
            "output_contract_version": (
                experimental.OUTPUT_CONTRACT_VERSION
                if condition == "citation_schema"
                else "json-mode-baseline"
            ),
            "provider_call_count": len(calls),
            "provider_calls": calls,
            "response": response,
            "duration_seconds": round(perf_counter() - started, 6),
        })

        print(
            json.dumps(response, ensure_ascii=False, indent=2),
            flush=True,
        )

    report["recorded_at"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"citation-schema-diagnostic-{stamp}.json"

    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Saved: {path}")
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()