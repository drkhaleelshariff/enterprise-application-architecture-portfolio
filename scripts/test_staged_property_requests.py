"""Verify staged request preparation without model calls."""

import copy
import json
import unittest
from unittest.mock import Mock, patch

import staged_property_requests as staged


def ready_context():
    sources = [{
        "citation": "DOC-N-ACCESS-001:v1",
        "document_id": "DOC-N-ACCESS-001",
        "version": "1",
        "title": "Synthetic North policy",
        "text": "Use the North access portal.",
    }]
    return {
        "decision": "allow",
        "context_status": "ready",
        "sources": sources,
        "context": json.dumps({"sources": sources}),
    }


def empty_context(status):
    return {
        "decision": "deny" if status == "denied" else "allow",
        "context_status": status,
        "sources": [],
        "context": "",
    }


class StagedRequestTests(unittest.TestCase):
    def setUp(self):
        self.context = ready_context()
        self.renderer = Mock(return_value={
            "_debug_info": {"rendered_template": "synthetic rendered prompt"}
        })

    def prepare(self):
        return staged.prepare_request(
            "USR-001", "Where should requests go?",
            self.context, self.renderer,
        )

    def validate(self, prepared, context=None):
        return staged.validate_prepared(
            prepared, "USR-001", "Where should requests go?",
            self.context if context is None else context,
        )

    def test_ready_preparation_and_validation(self):
        prepared = self.prepare()
        payload = self.validate(prepared)
        self.renderer.assert_called_once()
        rendering = self.renderer.call_args.args[0]
        self.assertIs(rendering["_debug_render_only"], True)
        self.assertIs(rendering["think"], False)
        self.assertIs(payload["cache_prompt"], False)
        self.assertEqual(
            payload["json_schema"],
            staged.adapter.response_schema(json.loads(self.context["context"])),
        )

    def test_denied_and_no_evidence_skip_rendering(self):
        for status in ("denied", "no_evidence"):
            with self.subTest(status=status):
                render = Mock()
                context = empty_context(status)
                prepared = staged.prepare_request(
                    "USR-001", "Question", context, render
                )
                render.assert_not_called()
                self.assertIsNone(prepared["completion_request"])
                with self.assertRaises(ValueError):
                    staged.validate_prepared(
                        prepared, "USR-001", "Question", context
                    )

    def test_changed_access_decision_is_rejected(self):
        prepared = self.prepare()
        with self.assertRaises(ValueError):
            self.validate(prepared, empty_context("denied"))

    def test_changed_source_version_or_text_is_rejected(self):
        prepared = self.prepare()
        for field, value in (
            ("version", "2"),
            ("text", "Changed policy text."),
            ("citation", "DOC-N-ACCESS-001:v2"),
        ):
            with self.subTest(field=field):
                current = copy.deepcopy(self.context)
                current["sources"][0][field] = value
                current["context"] = json.dumps({
                    "sources": current["sources"]
                })
                with self.assertRaises(ValueError):
                    self.validate(prepared, current)

    def test_changed_identity_or_question_is_rejected(self):
        prepared = self.prepare()
        for identity, question in (
            ("USR-002", "Where should requests go?"),
            ("USR-001", "What fee applies?"),
        ):
            with self.subTest(identity=identity, question=question):
                with self.assertRaises(ValueError):
                    staged.validate_prepared(
                        prepared, identity, question, self.context
                    )

    def test_changed_adapter_configuration_is_rejected(self):
        prepared = self.prepare()
        with patch.dict(staged.adapter.OPTIONS, {"temperature": 0.5}):
            with self.assertRaises(ValueError):
                self.validate(prepared)

    def test_changed_payload_is_rejected(self):
        for field, value in (
            ("cache_prompt", True),
            ("n_predict", 800),
            ("prompt", "Different prompt"),
        ):
            with self.subTest(field=field):
                prepared = self.prepare()
                prepared["completion_request"][field] = value
                with self.assertRaises(ValueError):
                    self.validate(prepared)

    def test_recomputed_fingerprint_does_not_allow_changed_settings(self):
        prepared = self.prepare()
        prepared["completion_request"]["cache_prompt"] = True
        prepared["completion_request_fingerprint"] = staged.fingerprint(
            prepared["completion_request"]
        )
        with self.assertRaises(ValueError):
            self.validate(prepared)

    def test_invalid_rendering_response_is_rejected(self):
        for response in ({}, None, {"_debug_info": {
            "rendered_template": ""
        }}):
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    staged.prepare_request(
                        "USR-001", "Question", self.context,
                        Mock(return_value=response),
                    )

    def test_preparation_snapshots_context(self):
        prepared = self.prepare()
        self.context["sources"][0]["text"] = "Later mutation"
        self.assertEqual(
            prepared["context_result"]["sources"][0]["text"],
            "Use the North access portal.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)