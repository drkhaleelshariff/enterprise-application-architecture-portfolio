"""Test approved-source answers without invoking a language model."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from answer_approved_property_question import answer_approved_question

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"


class ApprovedAnswerTests(unittest.TestCase):
    def answer(
        self,
        provider,
        *,
        identity="USR-001",
        query="Where should North replacement access card requests go?",
        approval_path=APPROVALS,
    ):
        return answer_approved_question(
            identity,
            query,
            provider,
            document_folder=FIXTURES,
            approval_path=approval_path,
        )

    def test_provider_receives_only_eligible_policy(self):
        provider = Mock(return_value={
            "answer": "Use the North access portal.",
            "citations": ["DOC-N-ACCESS-001:v1"],
        })
        result = self.answer(provider)

        provider.assert_called_once()
        evidence = json.loads(provider.call_args.args[1])
        self.assertEqual(
            [s["citation"] for s in evidence["sources"]],
            ["DOC-N-ACCESS-001:v1"],
        )
        self.assertNotIn("999 credits", provider.call_args.args[1])
        self.assertEqual(result["status"], "answered")

    def test_unapproved_and_unauthorized_citations_are_rejected(self):
        for citation in (
            "DOC-N-NOTE-001:v1",
            "DOC-S-ACCESS-001:v1",
        ):
            with self.subTest(citation=citation):
                provider = Mock(return_value={
                    "answer": "A generated answer.",
                    "citations": [citation],
                })
                result = self.answer(provider)
                self.assertEqual(result, {
                    "status": "invalid_provider_response",
                    "answer": "",
                    "citations": [],
                })

    def test_missing_or_invalid_register_skips_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "approvals.json"

            for content in (None, "{", '{"schema_version":"2"}'):
                with self.subTest(content=content):
                    if content is not None:
                        path.write_text(content, encoding="utf-8")

                    provider = Mock()
                    result = self.answer(provider, approval_path=path)
                    self.assertEqual(result, {
                        "status": "unavailable",
                        "answer": "",
                        "citations": [],
                    })
                    provider.assert_not_called()

    def test_empty_approvals_skip_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "approvals.json"
            path.write_text(json.dumps({
                "schema_version": "1",
                "approved_sources": [],
            }), encoding="utf-8")

            provider = Mock()
            result = self.answer(provider, approval_path=path)

        self.assertEqual(result["status"], "no_evidence")
        self.assertEqual(result["citations"], [])
        provider.assert_not_called()

    def test_no_keyword_match_skips_provider(self):
        provider = Mock()
        result = self.answer(
            provider,
            query="photosynthesis chlorophyll",
        )
        self.assertEqual(result["status"], "no_evidence")
        self.assertEqual(result["citations"], [])
        provider.assert_not_called()

    def test_denied_identities_skip_provider(self):
        for identity in ("USR-004", "USR-005", "UNKNOWN"):
            with self.subTest(identity=identity):
                provider = Mock()
                result = self.answer(provider, identity=identity)
                self.assertEqual(result, {
                    "status": "denied",
                    "answer": "",
                    "citations": [],
                })
                provider.assert_not_called()

    def test_explicit_abstention_remains_supported(self):
        provider = Mock(return_value={
            "status": "abstain",
            "answer": "",
            "citations": [],
        })
        result = self.answer(
            provider,
            query="What replacement fee applies to North access cards?",
        )
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        provider.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)