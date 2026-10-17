"""Verify the experimental direct adapter without model calls."""

import hashlib
import json
import unittest
from unittest.mock import MagicMock, patch

import direct_schema_property_provider as adapter
from answer_property_question import ProviderUnavailable

CONTEXT = json.dumps({
    "sources": [{
        "citation": "DOC-N-ACCESS-001:v1",
        "document_id": "DOC-N-ACCESS-001",
        "version": "1",
        "title": "Synthetic policy",
        "text": "Submit requests through the North access portal.",
    }],
})
ANSWER = {
    "answer": "Use the North access portal.",
    "citations": ["DOC-N-ACCESS-001:v1"],
}
RENDER = {"_debug_info": {"rendered_template": "rendered test prompt"}}


_MISSING = object()


def completion(content=_MISSING, **changes):
    if content is _MISSING:
        generated_text = json.dumps(ANSWER)
    elif isinstance(content, dict):
        generated_text = json.dumps(content)
    else:
        # Preserve raw malformed text and invalid content types.
        generated_text = content

    result = {
        "content": generated_text,
        "stop": True,
        "stop_type": "eos",
        "truncated": False,
    }
    result.update(changes)
    return result


def connection(envelope, status=200):
    conn = MagicMock()
    response = conn.getresponse.return_value
    response.status = status
    response.read.return_value = json.dumps(envelope).encode("utf-8")
    return conn


class DirectProviderTests(unittest.TestCase):
    def invoke(self, rendered=RENDER, generated=None, diagnostics=None):
        first = connection(rendered)
        second = connection(completion() if generated is None else generated)
        with patch.object(
            adapter, "HTTPConnection", side_effect=[first, second]
        ) as factory:
            result = adapter.provider(
                "Where should requests go?", CONTEXT,
                diagnostics=diagnostics,
            )
        return result, first, second, factory

    def test_supported_answer_and_exact_request_controls(self):
        result, first, second, factory = self.invoke()
        self.assertEqual(result, ANSWER)
        self.assertEqual(
            [call.args[:2] for call in factory.call_args_list],
            [("127.0.0.1", 11434), ("127.0.0.1", 18081)],
        )
        rendering = json.loads(first.request.call_args.kwargs["body"])
        generating = json.loads(second.request.call_args.kwargs["body"])
        self.assertIs(rendering["_debug_render_only"], True)
        self.assertIs(rendering["think"], False)
        self.assertEqual(rendering["options"]["num_gpu"], 0)
        self.assertIs(generating["cache_prompt"], False)
        self.assertEqual(generating["prompt"], "rendered test prompt")
        self.assertEqual(generating["presence_penalty"], 1.5)
        self.assertEqual(
            generating["json_schema"],
            adapter.response_schema(json.loads(CONTEXT)),
        )
        first.close.assert_called_once()
        second.close.assert_called_once()

    def test_explicit_abstention_is_preserved(self):
        abstention = {"status": "abstain", "answer": "", "citations": []}
        result, *_ = self.invoke(generated=completion(abstention))
        self.assertEqual(result, abstention)

    def test_incomplete_and_truncated_completions_are_suppressed(self):
        for change in (
            {"stop": False},
            {"stop_type": "limit"},
            {"truncated": True},
            {"stopped_limit": True},
            {"content": None},
        ):
            with self.subTest(change=change):
                result, *_ = self.invoke(generated=completion(**change))
                self.assertEqual(result, {})

    def test_missing_completion_flags_are_suppressed(self):
        for field in ("stop", "stop_type", "truncated"):
            with self.subTest(field=field):
                envelope = completion()
                del envelope[field]
                result, *_ = self.invoke(generated=envelope)
                self.assertEqual(result, {})

    def test_malformed_and_duplicate_generated_json_are_suppressed(self):
        for content in (
            "not JSON",
            '{"answer":"first","answer":"second","citations":[]}',
        ):
            with self.subTest(content=content):
                result, *_ = self.invoke(
                    generated=completion(content=content)
                )
                self.assertEqual(result, {})

    def test_invalid_rendering_skips_generation(self):
        for envelope in ({}, {"_debug_info": None}, {
            "_debug_info": {"rendered_template": ""}
        }):
            with self.subTest(envelope=envelope):
                first = connection(envelope)
                with patch.object(
                    adapter, "HTTPConnection", return_value=first
                ) as factory:
                    with self.assertRaises(ProviderUnavailable):
                        adapter.provider("Question", CONTEXT)
                self.assertEqual(factory.call_count, 1)
                first.close.assert_called_once()

    def test_http_failures_at_each_stage_raise_unavailable(self):
        for stage in ("render", "completion"):
            with self.subTest(stage=stage):
                first = connection(RENDER, 500 if stage == "render" else 200)
                second = connection({}, 500)
                with patch.object(
                    adapter, "HTTPConnection", side_effect=[first, second]
                ):
                    with self.assertRaises(ProviderUnavailable):
                        adapter.provider("Question", CONTEXT)

    def test_transport_failure_at_each_stage_closes_connection(self):
        for stage in ("render", "completion"):
            with self.subTest(stage=stage):
                first = connection(RENDER)
                second = connection(completion())
                failing = first if stage == "render" else second
                failing.request.side_effect = TimeoutError("simulated timeout")
                with patch.object(
                    adapter, "HTTPConnection", side_effect=[first, second]
                ):
                    with self.assertRaises(ProviderUnavailable):
                        adapter.provider("Question", CONTEXT)
                failing.close.assert_called_once()

    def test_invalid_service_json_and_oversized_bodies_are_rejected(self):
        for raw in (
            b"not JSON",
            b'{"x":1,"x":2}',
            b"[]",
            b"x" * 1_048_577,
        ):
            with self.subTest(length=len(raw)):
                first = connection(RENDER)
                first.getresponse.return_value.read.return_value = raw
                with patch.object(
                    adapter, "HTTPConnection", return_value=first
                ) as factory:
                    with self.assertRaises(ProviderUnavailable):
                        adapter.provider("Question", CONTEXT)
                self.assertEqual(factory.call_count, 1)
                first.close.assert_called_once()

    def test_diagnostic_hashes_match_bytes_sent(self):
        diagnostics = []
        _, first, second, _ = self.invoke(diagnostics=diagnostics)
        entries = [
            entry for entry in diagnostics
            if "request_body_utf8" in entry
        ]
        self.assertEqual(len(entries), 2)
        for entry, conn in zip(entries, (first, second)):
            sent = conn.request.call_args.kwargs["body"]
            self.assertEqual(entry["request_body_utf8"].encode("utf-8"), sent)
            self.assertEqual(
                entry["request_body_sha256"],
                hashlib.sha256(sent).hexdigest(),
            )

    def test_success_records_separate_stage_durations(self):
        diagnostics = []
        with patch.object(
            adapter, "perf_counter",
            side_effect=[10.0, 12.5, 20.0, 27.25],
        ):
            self.invoke(diagnostics=diagnostics)

        timings = [
            entry for entry in diagnostics
            if entry.get("event") == "http_stage_finished"
        ]
        self.assertEqual(timings, [
            {
                "stage": "render",
                "event": "http_stage_finished",
                "duration_seconds": 2.5,
            },
            {
                "stage": "completion",
                "event": "http_stage_finished",
                "duration_seconds": 7.25,
            },
        ])

    def test_transport_failure_records_elapsed_time(self):
        diagnostics = []
        conn = connection(RENDER)
        conn.request.side_effect = TimeoutError("simulated timeout")

        with patch.object(adapter, "HTTPConnection", return_value=conn):
            with patch.object(
                adapter, "perf_counter", side_effect=[100.0, 280.0]
            ):
                with self.assertRaises(ProviderUnavailable):
                    adapter.post_json(
                        18081, "/completion", {},
                        "completion", diagnostics,
                    )

        self.assertEqual(diagnostics[-1], {
            "stage": "completion",
            "event": "http_stage_finished",
            "duration_seconds": 180.0,
        })
        self.assertTrue(any(
            entry.get("failure_stage") == "transport"
            for entry in diagnostics
        ))
        conn.close.assert_called_once()

    def test_http_failure_records_elapsed_time(self):
        diagnostics = []
        conn = connection({"error": "simulated failure"}, status=500)

        with patch.object(adapter, "HTTPConnection", return_value=conn):
            with patch.object(
                adapter, "perf_counter", side_effect=[5.0, 8.125]
            ):
                with self.assertRaises(ProviderUnavailable):
                    adapter.post_json(
                        11434, "/api/generate", {},
                        "render", diagnostics,
                    )

        self.assertEqual(diagnostics[-1], {
            "stage": "render",
            "event": "http_stage_finished",
            "duration_seconds": 3.125,
        })
        self.assertTrue(any(
            entry.get("http_status") == 500
            for entry in diagnostics
        ))
        conn.close.assert_called_once()

if __name__ == "__main__":
    unittest.main(verbosity=2)