"""Prepare experimental requests and check them against current evidence."""

import hashlib
import json

import direct_schema_property_provider as adapter


def fingerprint(value):
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def configuration():
    return {
        "model": adapter.MODEL,
        "think": adapter.THINK,
        "system_prompt": adapter.SYSTEM_PROMPT,
        "prompt_version": adapter.PROMPT_VERSION,
        "output_contract_version": adapter.OUTPUT_CONTRACT_VERSION,
        "options": dict(adapter.OPTIONS),
        "cache_prompt": False,
    }


def completion_request(prompt, schema):
    payload = {
        "prompt": prompt,
        "stream": False,
        "n_predict": adapter.OPTIONS["num_predict"],
        "n_keep": adapter.OPTIONS["num_keep"],
        "json_schema": schema,
        "cache_prompt": False,
    }
    for name in (
        "temperature", "top_k", "top_p", "min_p", "typical_p",
        "repeat_penalty", "repeat_last_n", "presence_penalty",
        "frequency_penalty", "seed", "stop",
    ):
        payload[name] = adapter.OPTIONS[name]
    return payload


def prepare_request(identity_id, query, context_result, render):
    """Render only ready evidence; render is an injected callable."""
    # Snapshot inputs so later caller mutations cannot change the preparation.
    prepared = json.loads(json.dumps({
        "identity_id": identity_id,
        "question": query,
        "context_result": context_result,
        "configuration": configuration(),
        "completion_request": None,
    }))

    status = context_result.get("context_status")
    if status in {"denied", "no_evidence"}:
        return prepared
    if status != "ready" or context_result.get("decision") != "allow":
        raise ValueError("Unexpected context decision or status")

    evidence = json.loads(context_result["context"])
    schema = adapter.response_schema(evidence)
    rendering_request = {
        "model": adapter.MODEL,
        "system": adapter.SYSTEM_PROMPT,
        "prompt": json.dumps({
            "question": query,
            "authorized_evidence": evidence,
        }, ensure_ascii=False),
        "format": schema,
        "stream": False,
        "think": adapter.THINK,
        "options": dict(adapter.OPTIONS),
        "_debug_render_only": True,
    }
    response = render(rendering_request)
    debug = response.get("_debug_info") if isinstance(response, dict) else None
    prompt = debug.get("rendered_template") if isinstance(debug, dict) else None
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("Missing rendered prompt")

    prepared["rendering_request"] = rendering_request
    prepared["rendered_prompt_sha256"] = hashlib.sha256(
        prompt.encode("utf-8")
    ).hexdigest()
    prepared["completion_request"] = completion_request(prompt, schema)
    prepared["completion_request_fingerprint"] = fingerprint(
        prepared["completion_request"]
    )
    return prepared


def validate_prepared(prepared, identity_id, query, current_context):
    """Check freshness; callers must obtain current_context through authorization."""
    if prepared["identity_id"] != identity_id or prepared["question"] != query:
        raise ValueError("Prepared identity or question differs")
    if prepared["configuration"] != configuration():
        raise ValueError("Prepared configuration is stale")
    if prepared["context_result"] != current_context:
        raise ValueError("Prepared evidence or access decision is stale")
    if (
        current_context.get("decision") != "allow"
        or current_context.get("context_status") != "ready"
    ):
        raise ValueError("Current evidence is not eligible for generation")

    payload = prepared["completion_request"]
    if not isinstance(payload, dict):
        raise ValueError("Missing prepared completion request")
    if fingerprint(payload) != prepared["completion_request_fingerprint"]:
        raise ValueError("Prepared request fingerprint differs")

    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        raise ValueError("Invalid prepared prompt")
    if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != prepared[
        "rendered_prompt_sha256"
    ]:
        raise ValueError("Prepared prompt hash differs")

    evidence = json.loads(current_context["context"])
    expected = completion_request(prompt, adapter.response_schema(evidence))
    if payload != expected:
        raise ValueError("Prepared generation settings or schema differ")
    return payload