"""Verify staged answering with controlled context and mock completions."""

import copy
import json
import unittest
from unittest.mock import Mock, patch

import answer_staged_property_question as boundary
from answer_property_question import ProviderUnavailable
from staged_property_requests import prepare_request

QUERY = "Where should North requests go?"
CITATION = "DOC-N-ACCESS-001:v1"


def ready_context():
    sources = [{
        "citation": CITATION,
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


def envelope(answer):
    return {
        "content": json.dumps(answer),
        "stop": True,
        "stop_type": "eos",
        "truncated": False,
    }


class StagedAnswerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.context = ready_context()
        self.prepared = prepare_request(
            "USR-001", QUERY, self.context,
            Mock(return_value={
                "_debug_info": {"rendered_template": "synthetic prompt"}
            }),
        )
        self.completion = Mock(return_value=envelope({
            "answer": "Use the North access portal.",
            "citations": [CITATION],
        }))

    def invoke(self, current=None, prepared=None, query=QUERY):
        diagnostics = []
        with patch.object(
            boundary, "build_approved_context",
            return_value=self.context if current is None else current,
        ) as builder:
            response = boundary.answer_staged_question(
                self.prepared if prepared is None else prepared,
                "USR-001",
                query,
                document_folder="synthetic-documents",
                approval_path="synthetic-approvals",
                diagnostics=diagnostics,
                completion_function=self.completion,
            )
        return response, diagnostics, builder

    def test_current_context_is_rebuilt_and_valid_answer_accepted(self):
        response, _, builder = self.invoke()
        builder.assert_called_once()
        self.completion.assert_called_once()
        payload = self.completion.call_args.args[0]
        self.assertIs(payload["cache_prompt"], False)
        self.assertEqual(payload, self.prepared["completion_request"])
        self.assertEqual(response["status"], "answered")
        self.assertEqual(response["citations"], [CITATION])

    def test_current_denial_overrides_prepared_access(self):
        response, _, _ = self.invoke(current={
            "decision": "deny",
            "context_status": "denied",
            "sources": [],
            "context": "",
        })
        self.completion.assert_not_called()
        self.assertEqual(response["status"], "denied")
        self.assertEqual(response["citations"], [])

    def test_current_no_evidence_skips_completion(self):
        response, _, _ = self.invoke(current={
            "decision": "allow",
            "context_status": "no_evidence",
            "sources": [],
            "context": "",
        })
        self.completion.assert_not_called()
        self.assertNotEqual(response["status"], "answered")
        self.assertEqual(response["citations"], [])

    def test_changed_evidence_skips_completion(self):
        current = copy.deepcopy(self.context)
        current["sources"][0]["text"] = "Updated policy text."
        current["context"] = json.dumps({"sources": current["sources"]})
        response, _, _ = self.invoke(current=current)
        self.completion.assert_not_called()
        self.assertNotEqual(response["status"], "answered")

    def test_changed_question_skips_completion(self):
        response, _, _ = self.invoke(query="What fee applies?")
        self.completion.assert_not_called()
        self.assertNotEqual(response["status"], "answered")

    def test_tampered_payload_skips_completion(self):
        prepared = copy.deepcopy(self.prepared)
        prepared["completion_request"]["cache_prompt"] = True
        response, _, _ = self.invoke(prepared=prepared)
        self.completion.assert_not_called()
        self.assertNotEqual(response["status"], "answered")

    def test_ineligible_citation_is_rejected(self):
        self.completion.return_value = envelope({
            "answer": "An unsupported answer.",
            "citations": ["DOC-S-ACCESS-001:v1"],
        })
        response, _, _ = self.invoke()
        self.assertEqual(response["status"], "invalid_provider_response")
        self.assertEqual(response["answer"], "")
        self.assertEqual(response["citations"], [])

    def test_explicit_abstention_is_supported(self):
        self.completion.return_value = envelope({
            "status": "abstain", "answer": "", "citations": []
        })
        response, diagnostics, _ = self.invoke()
        self.assertEqual(response["status"], "abstained")
        self.assertEqual(response["citations"], [])
        self.assertEqual(diagnostics[-1]["stop_type"], "eos")

    def test_provider_failure_returns_unavailable(self):
        self.completion.side_effect = ProviderUnavailable("simulated failure")
        response, _, _ = self.invoke()
        self.assertEqual(response["status"], "unavailable")
        self.assertEqual(response["answer"], "")
        self.assertEqual(response["citations"], [])

    def test_incomplete_completion_is_suppressed(self):
        self.completion.return_value = envelope({
            "answer": "Use the North access portal.",
            "citations": [CITATION],
        })
        self.completion.return_value["stop"] = False
        response, _, _ = self.invoke()
        self.assertEqual(response["status"], "invalid_provider_response")
        self.assertEqual(response["answer"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)