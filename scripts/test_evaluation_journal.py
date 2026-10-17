"""Verify evaluation journal persistence without model calls."""

import json
import tempfile
import unittest
from pathlib import Path

from evaluation_journal import EvaluationJournal


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "run.jsonl"

    def read_events(self):
        return [
            json.loads(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
        ]

    def test_each_event_is_readable_before_journal_closes(self):
        with EvaluationJournal(self.path) as journal:
            journal.append("started", planned_cases=2)
            self.assertEqual(len(self.read_events()), 1)
            journal.append(
                "case_completed",
                record={"case_id": "CASE-1", "response": {"status": "denied"}},
            )
            events = self.read_events()
            self.assertEqual(len(events), 2)
            self.assertEqual(
                events[1]["fields"]["record"]["response"]["status"], "denied"
            )

    def test_existing_evidence_is_not_overwritten(self):
        self.path.write_text("original evidence\n", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            EvaluationJournal(self.path)
        self.assertEqual(
            self.path.read_text(encoding="utf-8"), "original evidence\n"
        )

    def test_completed_event_survives_later_exception(self):
        with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
            with EvaluationJournal(self.path) as journal:
                journal.append(
                    "case_completed", record={"case_id": "CASE-1"}
                )
                raise RuntimeError("simulated interruption")
        events = self.read_events()
        self.assertEqual(events[0]["fields"]["record"]["case_id"], "CASE-1")

    def test_serialization_failure_preserves_prior_events(self):
        with EvaluationJournal(self.path) as journal:
            journal.append("started")
            with self.assertRaises(TypeError):
                journal.append("invalid", value=object())
            self.assertEqual(len(self.read_events()), 1)
            journal.append("case_started", case_id="CASE-1")
        self.assertEqual(len(self.read_events()), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)