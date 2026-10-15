"""Verify source approval and authorization before ranking."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_approved_context as subject
from source_approvals import load_approvals

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = (
    ROOT / "projects" / "05-permission-aware-rag"
    / "data" / "robustness_v1"
)
APPROVALS = FIXTURES / "source_approvals.json"


class ApprovedContextTests(unittest.TestCase):
    def build(self, identity="USR-001", approval_path=APPROVALS):
        return subject.build_approved_context(
            identity,
            "replacement access card",
            document_folder=FIXTURES,
            approval_path=approval_path,
        )

    def test_only_authorized_approved_text_reaches_ranking(self):
        real_rank = subject.rank_documents
        with patch.object(
            subject, "rank_documents", wraps=real_rank
        ) as rank:
            result = self.build()

        ranked = rank.call_args.args[1]
        self.assertEqual(
            [d["document_id"] for d in ranked],
            ["DOC-N-ACCESS-001"],
        )
        self.assertEqual(result["context_status"], "ready")
        self.assertEqual(
            [s["citation"] for s in result["sources"]],
            ["DOC-N-ACCESS-001:v1"],
        )
        self.assertNotIn("999 credits", result["context"])
        self.assertNotIn("DOC-N-NOTE-001", result["context"])
        self.assertNotIn("DOC-S-ACCESS-001", result["context"])

    def test_south_approval_does_not_override_entity_access(self):
        result = self.build("USR-002")
        self.assertEqual(
            [s["citation"] for s in result["sources"]],
            ["DOC-S-ACCESS-001:v1"],
        )

    def test_both_entity_identity_receives_both_policies(self):
        result = self.build("USR-003")
        self.assertEqual(
            {s["citation"] for s in result["sources"]},
            {"DOC-N-ACCESS-001:v1", "DOC-S-ACCESS-001:v1"},
        )

    def test_denied_identities_skip_documents_approvals_and_ranking(self):
        for identity in ("USR-004", "USR-005", "UNKNOWN"):
            with self.subTest(identity=identity):
                with (
                    patch.object(subject, "load_documents") as documents,
                    patch.object(subject, "load_approvals") as approvals,
                    patch.object(subject, "rank_documents") as rank,
                ):
                    result = self.build(identity)

                self.assertEqual(result, {
                    "decision": "deny",
                    "context_status": "denied",
                    "sources": [],
                    "context": "",
                })
                documents.assert_not_called()
                approvals.assert_not_called()
                rank.assert_not_called()

    def test_empty_and_wrong_version_approvals_exclude_sources(self):
        for entries in (
            [],
            [{"document_id": "DOC-N-ACCESS-001", "version": "2"}],
        ):
            with self.subTest(entries=entries):
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / "approvals.json"
                    path.write_text(json.dumps({
                        "schema_version": "1",
                        "approved_sources": entries,
                    }), encoding="utf-8")

                    real_rank = subject.rank_documents
                    with patch.object(
                        subject, "rank_documents", wraps=real_rank
                    ) as rank:
                        result = self.build(approval_path=path)

                self.assertEqual(rank.call_args.args[1], [])
                self.assertEqual(result, {
                    "decision": "allow",
                    "context_status": "no_evidence",
                    "sources": [],
                    "context": "",
                })

    def test_invalid_registers_fail_before_ranking(self):
        invalid = [
            '{"schema_version":"1","schema_version":"1",'
            '"approved_sources":[]}',
            '{"schema_version":"2","approved_sources":[]}',
            '{"schema_version":"1","approved_sources":{}}',
            '{"schema_version":"1","approved_sources":[],'
            '"extra":true}',
            '{"schema_version":"1","approved_sources":['
            '{"document_id":"DOC-N-ACCESS-001","version":"01"}]}',
            '{"schema_version":"1","approved_sources":['
            '{"document_id":"DOC-N-ACCESS-001","version":"1"},'
            '{"document_id":"DOC-N-ACCESS-001","version":"1"}]}',
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "approvals.json"
            for content in invalid:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with patch.object(subject, "rank_documents") as rank:
                        with self.assertRaises(ValueError):
                            self.build(approval_path=path)
                    rank.assert_not_called()

    def test_missing_register_fails_before_ranking(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "missing.json"
            with patch.object(subject, "rank_documents") as rank:
                with self.assertRaises(OSError):
                    self.build(approval_path=path)
            rank.assert_not_called()

    def test_deleted_document_is_excluded_even_if_approved(self):
        with (FIXTURES / "documents.json").open(
            encoding="utf-8-sig"
        ) as handle:
            corpus = json.load(handle)

        for document in corpus["documents"]:
            if document["document_id"] == "DOC-N-ACCESS-001":
                document["status"] = "deleted"

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            (path / "documents.json").write_text(
                json.dumps(corpus), encoding="utf-8"
            )
            real_rank = subject.rank_documents
            with patch.object(
                subject, "rank_documents", wraps=real_rank
            ) as rank:
                result = subject.build_approved_context(
                    "USR-001",
                    "replacement access card",
                    document_folder=path,
                    approval_path=APPROVALS,
                )

        self.assertEqual(rank.call_args.args[1], [])
        self.assertEqual(result["context_status"], "no_evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)