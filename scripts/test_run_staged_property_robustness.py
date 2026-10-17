"""Verify staged evaluation orchestration using mocked services."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import run_staged_property_robustness as runner


class StagedRunnerTests(unittest.TestCase):
    def exercise(self, root, mode="complete"):
        fixtures = root / "data"
        fixtures.mkdir()
        output = root / "evidence"
        cases = [
            {
                "case_id": f"ROBUST-{number:03}",
                "identity_id": "SYNTHETIC",
                "question": f"Question {number}",
                "expected_behavior": "deny" if number == 8 else "abstain",
                "required_facts": [],
                "required_citations": [],
                "review_note": "Orchestration test only",
            }
            for number in range(1, 9)
        ]
        cases_bytes = json.dumps({
            "schema_version": "1", "cases": cases
        }).encode("utf-8")
        (fixtures / "cases.json").write_bytes(cases_bytes)

        evidence = {"sources": [{"citation": "SYNTHETIC:v1"}]}
        preparation = {
            "schema_version": "1",
            "execution_status": "completed",
            "generation_performed": False,
            "configuration": runner.configuration(),
            "cases_file_sha256": hashlib.sha256(cases_bytes).hexdigest(),
            "model": runner.adapter.MODEL,
            "model_digest": "test-digest",
            "ollama_version": {"version": "test"},
            "cases": [
                {
                    "case": case,
                    "prepared": {
                        "context_result": {
                            "context": json.dumps(evidence)
                        }
                    },
                }
                for case in cases
            ],
        }
        if mode == "changed_cases":
            preparation["cases_file_sha256"] = "different"
        preparation_path = root / "preparation.json"
        preparation_path.write_text(json.dumps(preparation), encoding="utf-8")

        residency_checks = 0

        def fake_get(url):
            nonlocal residency_checks
            if url.endswith("/api/version"):
                return {"version": "test"}
            if url.endswith("/health"):
                return {"status": "ok"}
            if url.endswith("/api/ps"):
                residency_checks += 1
                loaded = (
                    mode == "loaded_initially"
                    or mode == "loaded_after_case" and residency_checks == 3
                )
                return {"models": [{"name": "unexpected"}] if loaded else []}
            self.fail(f"Unexpected service URL: {url}")

        def fake_answer(prepared, identity, query, **kwargs):
            if query == "Question 8":
                return {"status": "denied", "answer": "", "citations": []}
            kwargs["completion_function"](
                {"cache_prompt": False}, kwargs["diagnostics"]
            )
            return {"status": "abstained", "answer": "", "citations": []}

        def fake_post(port, path, payload, stage, diagnostics):
            self.assertEqual((port, path, stage), (
                18081, "/completion", "completion"
            ))
            self.assertIs(payload["cache_prompt"], False)
            diagnostics.append({"stage": stage, "mock_record": True})
            return {}

        with ExitStack() as stack:
            for name, value in {
                "ROOT": root,
                "FIXTURES": fixtures,
                "APPROVALS": fixtures / "approvals.json",
                "OUTPUT": output,
            }.items():
                stack.enter_context(patch.object(runner, name, value))
            stack.enter_context(patch.object(
                runner.subprocess, "run",
                return_value=SimpleNamespace(stdout=""),
            ))
            stack.enter_context(patch.object(
                runner, "repository_commit", return_value="test-commit"
            ))
            stack.enter_context(patch.object(
                runner, "model_metadata",
                return_value={
                    "model": runner.adapter.MODEL,
                    "digest": "test-digest",
                },
            ))
            stack.enter_context(patch.object(
                runner, "memory_snapshot", return_value={"mock": True}
            ))
            stack.enter_context(patch.object(
                runner, "get_json", side_effect=fake_get
            ))
            answer_mock = stack.enter_context(patch.object(
                runner, "answer_staged_question", side_effect=fake_answer
            ))
            post_mock = stack.enter_context(patch.object(
                runner.adapter, "post_json", side_effect=fake_post
            ))
            with redirect_stdout(io.StringIO()):
                if mode == "complete":
                    runner.run(preparation_path)
                else:
                    with self.assertRaises((ValueError, RuntimeError)):
                        runner.run(preparation_path)

        return output, answer_mock.call_count, post_mock.call_count

    def test_complete_run_journals_all_cases_and_skips_denied_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            output, answers, completions = self.exercise(Path(directory))
            self.assertEqual((answers, completions), (8, 7))
            reports = list(output.glob("*.json"))
            journals = list(output.glob("*.jsonl"))
            self.assertEqual((len(reports), len(journals)), (1, 1))
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in journals[0].read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(
                [event["fields"]["record"] for event in events
                 if event["event_type"] == "case_completed"],
                report["cases"],
            )
            self.assertEqual(report["cases"][-1]["provider_call_count"], 0)
            self.assertNotIn("authorized_evidence", report["cases"][-1])
            self.assertEqual(report["review_status"], "not_reviewed")
            self.assertEqual(events[-1]["event_type"], "run_completed")
            self.assertEqual(sum(
                event["event_type"] == "residency_checked"
                for event in events
            ), 8)

    def test_initial_loaded_model_prevents_all_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            output, answers, completions = self.exercise(
                Path(directory), "loaded_initially"
            )
            self.assertEqual((answers, completions), (0, 0))
            self.assertFalse(output.exists())

    def test_changed_case_definitions_prevent_all_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            output, answers, completions = self.exercise(
                Path(directory), "changed_cases"
            )
            self.assertEqual((answers, completions), (0, 0))
            self.assertFalse(output.exists())

    def test_post_case_residency_failure_preserves_completed_record(self):
        with tempfile.TemporaryDirectory() as directory:
            output, answers, completions = self.exercise(
                Path(directory), "loaded_after_case"
            )
            self.assertEqual((answers, completions), (1, 1))
            self.assertEqual(list(output.glob("*.json")), [])
            journal = next(output.glob("*.jsonl"))
            events = [
                json.loads(line)
                for line in journal.read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(
                [event["event_type"] for event in events],
                ["run_started", "case_started",
                 "case_completed", "run_interrupted"],
            )
            self.assertEqual(
                events[2]["fields"]["record"]["case_id"], "ROBUST-001"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)