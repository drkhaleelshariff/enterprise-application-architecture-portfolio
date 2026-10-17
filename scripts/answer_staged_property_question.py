"""Answer from a prepared prompt only after fresh context validation."""

import json

import direct_schema_property_provider as adapter
from answer_property_question import answer_question
from build_approved_context import build_approved_context
from retrieve_documents import IDENTITY_DATA
from staged_property_requests import validate_prepared


def direct_completion(payload, diagnostics):
    return adapter.post_json(
        18081, "/completion", payload, "completion", diagnostics
    )


def answer_staged_question(
    prepared,
    identity_id,
    query,
    *,
    document_folder,
    approval_path,
    identity_folder=IDENTITY_DATA,
    diagnostics=None,
    completion_function=direct_completion,
):
    validated = {}

    def context_builder(current_identity, current_query, **folders):
        current = build_approved_context(
            current_identity,
            current_query,
            approval_path=approval_path,
            **folders,
        )
        # Current denial or no evidence is handled by the shared boundary.
        # A formerly ready preparation does not override either decision.
        if current.get("context_status") == "ready":
            payload = validate_prepared(
                prepared, current_identity, current_query, current
            )
            # Snapshot the validated request before handing it to the provider.
            validated["payload"] = json.loads(json.dumps(payload))
            validated["context"] = current["context"]
        return current

    def provider(current_query, context):
        if current_query != query or context != validated.get("context"):
            raise ValueError("Provider inputs differ from validated evidence")

        result = completion_function(validated["payload"], diagnostics)
        if not isinstance(result, dict):
            return {}

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
            return json.loads(content, object_pairs_hook=adapter.unique_object)
        except (ValueError, RecursionError):
            return {}

    return answer_question(
        identity_id,
        query,
        provider,
        identity_folder=identity_folder,
        document_folder=document_folder,
        context_builder=context_builder,
    )