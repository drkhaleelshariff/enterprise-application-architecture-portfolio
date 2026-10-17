"""Experimental direct llama-server generation without prefix reuse."""

import hashlib
import json
from http.client import HTTPConnection, HTTPException

from answer_property_question import ProviderUnavailable
from ollama_schema_property_provider import (
    MODEL,
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    THINK,
    response_schema,
    unique_object,
)

OUTPUT_CONTRACT_VERSION = "property-citation-schema-v1"
ADAPTER_VERSION = "direct-schema-no-prefix-reuse-v1"
TIMEOUT_SECONDS = 180

OPTIONS = {
    "temperature": 0,
    "num_ctx": 4096,
    "num_predict": 400,
    "num_gpu": 0,
    "num_keep": 4,
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
}


def post_json(port, path, payload, stage, diagnostics):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if diagnostics is not None:
        diagnostics.append({
            "stage": stage,
            "request_body_utf8": body.decode("utf-8"),
            "request_body_sha256": hashlib.sha256(body).hexdigest(),
        })

    connection = HTTPConnection(
        "127.0.0.1", port, timeout=TIMEOUT_SECONDS
    )
    try:
        connection.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        raw = response.read(1_048_577)

        if diagnostics is not None:
            diagnostics.append({
                "stage": stage,
                "http_status": response.status,
                "response_body_excerpt": raw[:4096].decode(
                    "utf-8", errors="replace"
                ),
            })

        if response.status != 200:
            raise ProviderUnavailable(f"{stage} HTTP failure")
        if len(raw) > 1_048_576:
            raise ProviderUnavailable(f"{stage} response exceeded limit")

        try:
            result = json.loads(raw, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise ProviderUnavailable(f"{stage} invalid JSON") from exc

        if not isinstance(result, dict):
            raise ProviderUnavailable(f"{stage} invalid envelope")
        return result
    except (OSError, HTTPException) as exc:
        if diagnostics is not None:
            diagnostics.append({
                "stage": stage,
                "failure_stage": "transport",
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            })
        raise ProviderUnavailable(f"{stage} unavailable") from exc
    finally:
        connection.close()


def provider(query, context, *, diagnostics=None):
    evidence = json.loads(context)
    schema = response_schema(evidence)

    rendered = post_json(
        11434,
        "/api/generate",
        {
            "model": MODEL,
            "system": SYSTEM_PROMPT,
            "prompt": json.dumps({
                "question": query,
                "authorized_evidence": evidence,
            }, ensure_ascii=False),
            "format": schema,
            "stream": False,
            "think": THINK,
            "options": OPTIONS,
            "_debug_render_only": True,
        },
        "render",
        diagnostics,
    )
    debug = rendered.get("_debug_info")
    prompt = debug.get("rendered_template") if isinstance(debug, dict) else None
    if not isinstance(prompt, str) or not prompt:
        raise ProviderUnavailable("Missing rendered prompt")

    payload = {
        "prompt": prompt,
        "stream": False,
        "n_predict": OPTIONS["num_predict"],
        "n_keep": OPTIONS["num_keep"],
        "json_schema": schema,
        "cache_prompt": False,
    }
    for name in (
        "temperature", "top_k", "top_p", "min_p", "typical_p",
        "repeat_penalty", "repeat_last_n", "presence_penalty",
        "frequency_penalty", "seed", "stop",
    ):
        payload[name] = OPTIONS[name]

    result = post_json(
        18081, "/completion", payload, "completion", diagnostics
    )
    content = result.get("content")
    if diagnostics is not None:
        diagnostics.append({
            "stage": "completion",
            "generated_text": content,
            "stop": result.get("stop"),
            "stop_type": result.get("stop_type"),
            "truncated": result.get("truncated"),
            "timings": result.get("timings"),
            "generation_settings": result.get("generation_settings"),
        })

    if (
        result.get("stop") is not True
        or result.get("stop_type") not in {"eos", "word"}
        or result.get("truncated") is not False
        or result.get("stopped_limit") is True
        or not isinstance(content, str)
    ):
        return {}

    try:
        return json.loads(content, object_pairs_hook=unique_object)
    except (ValueError, RecursionError):
        return {}