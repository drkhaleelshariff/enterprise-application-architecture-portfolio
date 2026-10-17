"""Test direct-runner journals with temporary files and mocked services."""

import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import run_direct_property_robustness as runner

EVIDENCE = {
    "sources": [{
        "document_id": "DOC-N-ACCESS-001",
        "version": "1",
        "citation": "DOC-N-ACCESS-001:v1",
        "title": "Synthetic policy",
        "text": "Synthetic evidence.",
    }],
}


class DirectJournalIntegrationTests(unittest.TestCase):
    def exercise(self, root, interrupt=False):
        fixtures = root / "data"
        fixtures.mkdir()
        output = root / "evidence"
        cases = [
            {
                "case_id": f"CASE-{number}",
                "identity_id": "SYNTHETIC",
                "question": f"Question {number}",
                "expected_behavior": "deny" if number == 2 else "abstain",
                "required_facts": [],
                "required_citations": [],
                "review_note": "Integration test only",
            }
            for number in (1, 2, 3)
        ]
        (fixtures / "cases.json").write_text(
            json.dumps({"schema_version": "1", "cases": cases}),
            encoding="utf-8",
        )

        def fake_provider(query, context, *, diagnostics=None):
            diagnostics.append({
                "stage": "completion",
                "generated_text": '{"status":"abstain","answer":"","citations":[]}',
            })
            return {"status": "abstain", "answer": "", "citations": []}

        def fake_answer(identity, question, provider, **kwargs):
            if question == "Question 2":
                if interrupt:
                    raise KeyboardInterrupt("simulated interruption")
                return {"status": "denied", "answer": "", "citations": []}
            provider(question, json.dumps(EVIDENCE))
            return {"status": "abstained", "answer": "", "citations": []}

        with ExitStack() as stack:
            replacements = {
                "ROOT": root,
                "FIXTURES": fixtures,
                "APPROVALS": fixtures / "approvals.json",
                "OUTPUT": output,
            }
            for name, value in replacements.items():
                stack.enter_context(patch.object(runner, name, value))
            stack.enter_context(patch.object(
                runner.subprocess, "run",
                return_value=SimpleNamespace(stdout=""),
            ))
            stack.enter_context(patch.object(
                runner, "get_json",
                side_effect=[{"version": "test"}, {"status": "ok"}],
            ))
            stack.enter_context(patch.object(
                runner, "model_metadata",
                return_value={"model": runner.adapter.MODEL},
            ))
            stack.enter_context(patch.object(
                runner, "load_approvals",
                return_value={("DOC-N-ACCESS-001", "1")},
            ))
            stack.enter_context(patch.object(
                runner, "repository_commit", return_value="test-commit"
            ))
            stack.enter_context(patch(
                "evaluate_property_answers.repository_commit",
                return_value="test-commit",
            ))
            stack.enter_context(patch.object(
                runner, "answer_approved_question", side_effect=fake_answer
            ))
            adapter_mock = stack.enter_context(patch.object(
                runner.adapter, "provider", side_effect=fake_provider
            ))
            console = io.StringIO()
            with redirect_stdout(console):
                if interrupt:
                    with self.assertRaises(KeyboardInterrupt):
                        runner.main()
                else:
                    runner.main()

        journals = list(output.glob("*.jsonl"))
        self.assertEqual(len(journals), 1)
        events = [
            json.loads(line)
            for line in journals[0].read_text(encoding="utf-8").splitlines()
        ]
        return output, events, console.getvalue(), adapter_mock.call_count

    def test_completed_journal_matches_final_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output, events, console, calls = self.exercise(Path(directory))
            reports = list(output.glob("*.json"))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            completed = [
                event["fields"]["record"]
                for event in events
                if event["event_type"] == "case_completed"
            ]
            self.assertEqual(completed, report["cases"])
            self.assertEqual(calls, 2)
            self.assertEqual(events[-1]["event_type"], "evaluation_finished")
            self.assertEqual(
                completed[0]["provider_calls"][0]["authorized_evidence"],
                EVIDENCE,
            )
            self.assertIn(
                "generated_text",
                completed[0]["provider_calls"][0]["diagnostics"][0],
            )
            self.assertEqual(completed[1]["provider_call_count"], 0)
            self.assertEqual(completed[1]["provider_calls"], [])
            self.assertIn("Starting CASE-1", console)
            self.assertIn("Saved CASE-3", console)
            self.assertEqual(report["review_status"], "not_reviewed")
            self.assertTrue((Path(directory) / report["journal_file"]).is_file())

    def test_interruption_preserves_completed_case_and_inflight_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            output, events, console, calls = self.exercise(
                Path(directory), interrupt=True
            )
            self.assertEqual(list(output.glob("*.json")), [])
            self.assertEqual(calls, 1)
            self.assertEqual(
                [event["event_type"] for event in events],
                [
                    "run_started",
                    "case_started",
                    "case_completed",
                    "case_started",
                    "run_interrupted",
                ],
            )
            self.assertEqual(
                events[2]["fields"]["record"]["case_id"], "CASE-1"
            )
            self.assertEqual(events[3]["fields"]["case_id"], "CASE-2")
            self.assertEqual(
                events[-1]["fields"]["error_type"], "KeyboardInterrupt"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)