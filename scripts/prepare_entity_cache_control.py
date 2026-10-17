"""Prepare rendered prompts and explicit cache-control requests."""

import hashlib
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

import ollama_schema_property_provider as adapter
from build_approved_context import build_approved_context
from diagnose_entity_predecessor import FIXTURES, APPROVALS
from evaluate_property_answers import ROOT, repository_commit
from run_property_evaluation import OUTPUT

ENDPOINT = "http://127.0.0.1:11434"


def post(path, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        ENDPOINT + path,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=180) as response:
        return json.load(response)


def main():
    with (FIXTURES / "cases.json").open(encoding="utf-8-sig") as handle:
        cases = {
            case["case_id"]: case
            for case in json.load(handle)["cases"]
        }

    model_info = post("/api/show", {"model": adapter.MODEL})
    report = {
        "experiment": "entity-cache-control-preparation",
        "repository_commit": repository_commit(),
        "model": adapter.MODEL,
        "prompt_version": adapter.PROMPT_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
        "model_parameters": model_info.get("parameters"),
        "generation_performed": False,
        "review_status": "not_reviewed",
        "cases": [],
    }

    for case_id in ("ROBUST-001", "ROBUST-003"):
        case = cases[case_id]
        evidence = build_approved_context(
            case["identity_id"],
            case["question"],
            document_folder=FIXTURES,
            approval_path=APPROVALS,
        )
        if evidence["context_status"] != "ready":
            raise RuntimeError("Expected ready context")

        authorized_evidence = json.loads(evidence["context"])
        schema = adapter.response_schema(authorized_evidence)
        options = dict(adapter.OPTIONS)
        options["num_gpu"] = 0

        rendering_request = {
            "model": adapter.MODEL,
            "system": adapter.SYSTEM_PROMPT,
            "prompt": json.dumps({
                "question": case["question"],
                "authorized_evidence": authorized_evidence,
            }, ensure_ascii=False),
            "format": schema,
            "stream": False,
            "think": adapter.THINK,
            "options": options,
            "_debug_render_only": True,
        }
        rendered = post("/api/generate", rendering_request)
        prompt = rendered.get("_debug_info", {}).get("rendered_template")
        if not isinstance(prompt, str) or not prompt:
            raise RuntimeError("Missing rendered prompt")

        # Model parameters plus Ollama v0.40.4 defaults and adapter overrides.
        common = {
            "prompt": prompt,
            "stream": False,
            "n_predict": 400,
            "n_keep": 4,
            "temperature": 0,
            "top_k": 20,
            "top_p": 0.95,
            "min_p": 0,
            "typical_p": 1,
            "repeat_penalty": 1,
            "repeat_last_n": 64,
            "presence_penalty": 1.5,
            "frequency_penalty": 0,
            "seed": -1,
            "stop": [],
            "json_schema": schema,
        }
        variants = {
            label: dict(common, cache_prompt=enabled)
            for label, enabled in (("cache_on", True), ("cache_off", False))
        }
        report["cases"].append({
            "case": case,
            "authorized_evidence": authorized_evidence,
            "rendering_request": rendering_request,
            "rendering_response": rendered,
            "rendered_prompt_sha256": hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest(),
            "direct_completion_requests": variants,
        })
        print(f"Prepared {case_id}; no generation performed.", flush=True)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"entity-cache-control-preparation-{stamp}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Saved: {path}")
    print("Preparation only. Direct-runner equivalence is not established.")


if __name__ == "__main__":
    main()