"""Test twelve-case orchestration without contacting model services."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import run_staged_property_validation as runner


class ValidationRunnerTests(unittest.TestCase):
    def exercise(self, root, mode="complete"):
        fixtures = root / "data"
        fixtures.mkdir()
        output = root / "evidence"
        cases = [
            {
                "case_id": f"STVAL-{number:03d}",
                "identity_id": "SYNTHETIC",
                "question": f"Question {number}",
                "expected_behavior": "deny" if number == 11 else "abstain",
                "required_facts": [],
                "required_citations": [],
                "review_note": "Orchestration test only",
            }
            for number in range(1, 13)
        ]
        cases_bytes = json.dumps({
            "schema_version": "1", "cases": cases
        }).encode("utf-8")
        (fixtures / "cases.json").write_bytes(cases_bytes)
        for name, content in {
            "plan.md": "# Test plan\n",
            "documents.json": '{"schema_version":"1","documents":[]}',
            "source_approvals.json": (
                '{"schema_version":"1","approved_sources":[]}'
            ),
        }.items():
            (fixtures / name).write_text(content, encoding="utf-8")

        hashes = {
            name: hashlib.sha256((fixtures / name).read_bytes()).hexdigest()
            for name in (
                "plan.md", "cases.json", "documents.json",
                "source_approvals.json",
            )
        }
        evidence = {"sources": [{"citation": "SYNTHETIC:v1"}]}
        preparation = {
            "schema_version": "1",
            "experiment": "staged-property-validation-preparation",
            "suite_id": "staged-visitor-permit-validation-v1",
            "execution_status": "completed",
            "generation_performed": False,
            "configuration": runner.configuration(),
            "cases_file": "data/cases.json",
            "cases_file_sha256": hashlib.sha256(cases_bytes).hexdigest(),
            "fixture_sha256": hashes,
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
        elif mode == "changed_order":
            preparation["cases"].reverse()
        elif mode == "wrong_suite":
            preparation["suite_id"] = "another-suite"
        elif mode == "wrong_cases_path":
            preparation["cases_file"] = "other/cases.json"
        elif mode == "changed_configuration":
            preparation["configuration"] = {}
        elif mode.startswith("changed_fixture:"):
            name = mode.split(":", 1)[1]
            with (fixtures / name).open("a", encoding="utf-8") as handle:
                handle.write("\nChanged after preparation\n")

        preparation_path = root / "preparation.json"
        preparation_path.write_text(json.dumps(preparation), encoding="utf-8")
        residency_checks = 0

        def fake_get(url):
            nonlocal residency_checks
            if url.endswith("/api/version"):
                return {
                    "version": "changed" if mode == "changed_version" else "test"
                }
            if url.endswith("/health"):
                return {"status": "ok"}
            if url.endswith("/api/ps"):
                residency_checks += 1
                loaded = (
                    mode == "loaded_initially"
                    or (mode == "loaded_after_case" and residency_checks == 3)
                )
                return {"models": [{"name": "unexpected"}] if loaded else []}
            self.fail(f"Unexpected service URL: {url}")

        def fake_answer(prepared, identity, query, **kwargs):
            self.assertEqual(kwargs["document_folder"], fixtures)
            self.assertEqual(
                kwargs["approval_path"], fixtures / "source_approvals.json"
            )
            if query == "Question 11":
                return {"status": "denied", "answer": "", "citations": []}
            kwargs["completion_function"](
                {"cache_prompt": False}, kwargs["diagnostics"]
            )
            return {"status": "abstained", "answer": "", "citations": []}

        def fake_post(port, path, payload, stage, diagnostics):
            self.assertEqual(
                (port, path, stage), (18081, "/completion", "completion")
            )
            self.assertIs(payload["cache_prompt"], False)
            diagnostics.append({"stage": stage, "mock_record": True})
            return {}

        with ExitStack() as stack:
            for name, value in {
                "ROOT": root,
                "FIXTURES": fixtures,
                "APPROVALS": fixtures / "source_approvals.json",
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
            metadata = stack.enter_context(patch.object(
                runner, "model_metadata",
                return_value={
                    "model": (
                        "different-model" if mode == "changed_model"
                        else runner.adapter.MODEL
                    ),
                    "digest": (
                        "different-digest" if mode == "changed_digest"
                        else "test-digest"
                    ),
                },
            ))
            stack.enter_context(patch.object(
                runner, "memory_snapshot", return_value={"mock": True}
            ))
            service = stack.enter_context(patch.object(
                runner, "get_json", side_effect=fake_get
            ))
            answer = stack.enter_context(patch.object(
                runner, "answer_staged_question", side_effect=fake_answer
            ))
            post = stack.enter_context(patch.object(
                runner.adapter, "post_json", side_effect=fake_post
            ))
            with redirect_stdout(io.StringIO()):
                if mode == "complete":
                    runner.run(preparation_path)
                else:
                    with self.assertRaises((ValueError, RuntimeError)):
                        runner.run(preparation_path)

        return {
            "output": output,
            "answers": answer.call_count,
            "completions": post.call_count,
            "metadata_calls": metadata.call_count,
            "service_calls": service.call_count,
            "hashes": hashes,
        }

    def test_complete_run_journals_twelve_cases_and_skips_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.exercise(Path(directory))
            self.assertEqual(
                (result["answers"], result["completions"]), (12, 11)
            )
            reports = list(result["output"].glob("*.json"))
            journals = list(result["output"].glob("*.jsonl"))
            self.assertEqual((len(reports), len(journals)), (1, 1))
            self.assertTrue(
                reports[0].name.startswith("answer-validation-staged-")
            )
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in journals[0].read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
            self.assertEqual(report["fixture_sha256"], result["hashes"])
            self.assertEqual(report["case_count"], 12)
            self.assertEqual(
                report["suite_id"], "staged-visitor-permit-validation-v1"
            )
            self.assertEqual(
                [event["fields"]["record"] for event in events
                 if event["event_type"] == "case_completed"],
                report["cases"],
            )
            denied = report["cases"][10]
            self.assertEqual(denied["case_id"], "STVAL-011")
            self.assertEqual(denied["provider_call_count"], 0)
            self.assertEqual(denied["diagnostics"], [])
            self.assertNotIn("authorized_evidence", denied)
            self.assertEqual(report["review_status"], "not_reviewed")
            self.assertEqual(events[-1]["event_type"], "run_completed")
            self.assertEqual(sum(
                event["event_type"] == "residency_checked"
                for event in events
            ), 12)

    def test_invalid_preparation_prevents_service_calls(self):
        modes = [
            "changed_cases", "changed_order", "wrong_suite",
            "wrong_cases_path", "changed_configuration",
            "changed_fixture:plan.md",
            "changed_fixture:documents.json",
            "changed_fixture:source_approvals.json",
        ]
        for mode in modes:
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as directory:
                    result = self.exercise(Path(directory), mode)
                    self.assertEqual(result["answers"], 0)
                    self.assertEqual(result["completions"], 0)
                    self.assertEqual(result["metadata_calls"], 0)
                    self.assertEqual(result["service_calls"], 0)
                    self.assertFalse(result["output"].exists())

    def test_model_digest_version_and_residency_changes_block_generation(self):
        for mode in (
            "changed_model", "changed_digest",
            "changed_version", "loaded_initially",
        ):
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as directory:
                    result = self.exercise(Path(directory), mode)
                    self.assertEqual(result["answers"], 0)
                    self.assertEqual(result["completions"], 0)
                    self.assertFalse(result["output"].exists())

    def test_post_case_residency_failure_preserves_completed_record(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.exercise(Path(directory), "loaded_after_case")
            self.assertEqual(
                (result["answers"], result["completions"]), (1, 1)
            )
            self.assertEqual(list(result["output"].glob("*.json")), [])
            journal = next(result["output"].glob("*.jsonl"))
            events = [
                json.loads(line)
                for line in journal.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [event["event_type"] for event in events],
                ["run_started", "case_started",
                 "case_completed", "run_interrupted"],
            )
            self.assertEqual(
                events[2]["fields"]["record"]["case_id"], "STVAL-001"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)