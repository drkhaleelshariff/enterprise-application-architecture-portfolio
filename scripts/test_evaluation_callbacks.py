"""Verify evaluation callbacks using temporary cases and a fake answer path."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluate_property_answers import evaluate


class EvaluationCallbackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cases_path = Path(self.temporary.name) / "cases.json"
        self.cases = [
            {
                "case_id": f"CASE-{number}",
                "identity_id": "SYNTHETIC",
                "question": f"Question {number}",
                "expected_behavior": "abstain",
                "required_facts": [],
                "required_citations": [],
                "review_note": "Callback test only",
            }
            for number in (1, 2)
        ]
        self.cases_path.write_text(
            json.dumps({"schema_version": "1", "cases": self.cases}),
            encoding="utf-8",
        )

    def run_evaluation(self, answer, **callbacks):
        with patch(
            "evaluate_property_answers.repository_commit",
            return_value="test-commit",
        ):
            return evaluate(
                lambda *args: self.fail("Provider must not be called"),
                provider_id="test",
                provider_configuration={},
                prompt_version="test",
                answer_function=answer,
                cases_path=self.cases_path,
                **callbacks,
            )

    def test_callbacks_run_in_order_and_receive_complete_records(self):
        events = []
        completed = []

        def answer(identity, question, provider, **kwargs):
            events.append(("answer", question))
            return {"status": "abstained", "answer": "", "citations": []}

        def on_completed(record):
            events.append(("completed", record["case_id"]))
            # Snapshot now, rather than relying on a later mutation.
            completed.append(json.loads(json.dumps(record)))

        report = self.run_evaluation(
            answer,
            on_case_start=lambda case_id: events.append(("start", case_id)),
            on_case_completed=on_completed,
        )
        self.assertEqual(events, [
            ("start", "CASE-1"),
            ("answer", "Question 1"),
            ("completed", "CASE-1"),
            ("start", "CASE-2"),
            ("answer", "Question 2"),
            ("completed", "CASE-2"),
        ])
        self.assertEqual(completed, report["cases"])
        self.assertEqual(report["review_status"], "not_reviewed")
        for record in completed:
            self.assertEqual(record["provider_call_count"], 0)
            self.assertEqual(record["review"]["decision"], "not_assessed")
            self.assertIn("duration_seconds", record)

    def test_completed_record_survives_later_answer_failure(self):
        completed = []

        def answer(identity, question, provider, **kwargs):
            if question == "Question 2":
                raise RuntimeError("simulated interruption")
            return {"status": "abstained", "answer": "", "citations": []}

        with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
            self.run_evaluation(
                answer,
                on_case_completed=lambda record: completed.append(
                    json.loads(json.dumps(record))
                ),
            )
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["case_id"], "CASE-1")

    def test_checkpoint_callback_failure_stops_before_next_case(self):
        answered = []

        def answer(identity, question, provider, **kwargs):
            answered.append(question)
            return {"status": "abstained", "answer": "", "citations": []}

        def failed_checkpoint(record):
            raise OSError("simulated checkpoint failure")

        with self.assertRaisesRegex(OSError, "checkpoint failure"):
            self.run_evaluation(
                answer, on_case_completed=failed_checkpoint
            )
        self.assertEqual(answered, ["Question 1"])

    def test_start_callback_failure_prevents_answer_execution(self):
        def failed_start(case_id):
            raise OSError("simulated start-record failure")

        def answer(*args, **kwargs):
            self.fail("Answer function must not run after callback failure")

        with self.assertRaisesRegex(OSError, "start-record failure"):
            self.run_evaluation(answer, on_case_start=failed_start)


if __name__ == "__main__":
    unittest.main(verbosity=2)