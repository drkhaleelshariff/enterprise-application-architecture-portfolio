"""Record matched and mismatched entity questions using the schema adapter."""

import json
import subprocess
from datetime import datetime, timezone
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

CONDITIONS = [
    {
        "condition": "north_question_north_evidence",
        "identity_id": "USR-001",
        "requested_entity": "North",
        "expected_source": "DOC-N-ACCESS-001:v1",
        "expected_behavior": "answer",
        "required_facts": ["three business days"],
        "required_citations": ["DOC-N-ACCESS-001:v1"],
    },
    {
        "condition": "south_question_north_evidence",
        "identity_id": "USR-001",
        "requested_entity": "South",
        "expected_source": "DOC-N-ACCESS-001:v1",
        "expected_behavior": "abstain",
        "required_facts": [],
        "required_citations": [],
    },
    {
        "condition": "south_question_south_evidence",
        "identity_id": "USR-002",
        "requested_entity": "South",
        "expected_source": "DOC-S-ACCESS-001:v1",
        "expected_behavior": "answer",
        "required_facts": ["four business hours"],
        "required_citations": ["DOC-S-ACCESS-001:v1"],
    },
    {
        "condition": "north_question_south_evidence",
        "identity_id": "USR-002",
        "requested_entity": "North",
        "expected_source": "DOC-S-ACCESS-001:v1",
        "expected_behavior": "abstain",
        "required_facts": [],
        "required_citations": [],
    },
]


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

    # model_metadata uses the baseline adapter's configuration.
    for name in (
        "MODEL", "THINK", "PROMPT_VERSION", "OPTIONS", "SYSTEM_PROMPT"
    ):
        if getattr(baseline, name) != getattr(adapter, name):
            raise RuntimeError(f"Adapter configuration differs: {name}")

    approved = load_approvals(APPROVALS)
    report = {
        "schema_version": "1",
        "experiment": "entity-applicability-four-conditions",
        "repository_commit": repository_commit(),
        "provider_configuration": model_metadata(),
        "adapter_module": adapter.__name__,
        "prompt_version": adapter.PROMPT_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
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

    contexts_by_identity = {}

    for condition in CONDITIONS:
        question = (
            "What is the target acknowledgement time for "
            f"{condition['requested_entity']} replacement access card requests?"
        )
        calls = []

        def captured_provider(query, context):
            evidence = json.loads(context)

            for source in evidence["sources"]:
                key = (source["document_id"], source["version"])
                if key not in approved:
                    raise RuntimeError("Unapproved source reached provider")

            citations = [
                source["citation"] for source in evidence["sources"]
            ]
            if citations != [condition["expected_source"]]:
                raise RuntimeError("Unexpected evidence for condition")

            identity_id = condition["identity_id"]
            if identity_id in contexts_by_identity:
                if evidence != contexts_by_identity[identity_id]:
                    raise RuntimeError("Evidence changed within identity pair")
            else:
                contexts_by_identity[identity_id] = evidence

            call = {
                "question": query,
                "authorized_evidence": evidence,
                "requested_format": adapter.response_schema(evidence),
                "diagnostics": [],
            }
            calls.append(call)

            return adapter.provider(
                query,
                context,
                diagnostics=call["diagnostics"],
            )

        print(f"Running {condition['condition']}...", flush=True)
        started = perf_counter()

        response = answer_approved_question(
            condition["identity_id"],
            question,
            captured_provider,
            document_folder=FIXTURES,
            approval_path=APPROVALS,
        )

        report["conditions"].append({
            **condition,
            "question": question,
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
    path = OUTPUT / f"entity-applicability-diagnostic-{stamp}.json"

    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Saved: {path}")
    print("Review status: not_reviewed. No quality scores assigned.")


if __name__ == "__main__":
    main()