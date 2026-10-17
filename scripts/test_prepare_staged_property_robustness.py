"""Test suite preparation with temporary files and mocked rendering."""

import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import prepare_staged_property_robustness as runner


def context_for(status):
    if status != "ready":
        return {
            "decision": "deny" if status == "denied" else "allow",
            "context_status": status,
            "sources": [],
            "context": "",
        }
    sources = [{
        "citation": "DOC-N-ACCESS-001:v1",
        "document_id": "DOC-N-ACCESS-001",
        "version": "1",
        "title": "Synthetic policy",
        "text": "Synthetic policy text.",
    }]
    return {
        "decision": "allow",
        "context_status": "ready",
        "sources": sources,
        "context": json.dumps({"sources": sources}),
    }


class PreparationIntegrationTests(unittest.TestCase):
    def exercise(self, root, fail_render=False):
        fixtures = root / "data"
        fixtures.mkdir()
        output = root / "evidence"
        cases = [
            {
                "case_id": f"ROBUST-{number:03}",
                "identity_id": "SYNTHETIC",
                "question": f"Question {number}",
                "expected_behavior": "answer",
                "required_facts": [],
                "required_citations": [],
                "review_note": "Preparation integration test",
            }
            for number in range(1, 9)
        ]
        (fixtures / "cases.json").write_text(
            json.dumps({"schema_version": "1", "cases": cases}),
            encoding="utf-8",
        )

        def fake_context(identity, query, **kwargs):
            number = int(query.split()[-1])
            status = (
                "denied" if number == 8
                else "no_evidence" if number == 7
                else "ready"
            )
            return context_for(status)

        render_count = 0

        def fake_render(port, path, payload, stage, diagnostics):
            nonlocal render_count
            render_count += 1
            if fail_render and render_count == 2:
                raise RuntimeError("simulated rendering failure")
            self.assertEqual((port, path, stage), (
                11434, "/api/generate", "render"
            ))
            self.assertIs(payload["_debug_render_only"], True)
            diagnostics.append({"stage": "render", "http_status": 200})
            return {
                "_debug_info": {
                    "rendered_template": f"synthetic prompt {render_count}"
                }
            }

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
                runner, "get_json", return_value={"version": "test"}
            ))
            stack.enter_context(patch.object(
                runner, "model_metadata",
                return_value={
                    "model": runner.adapter.MODEL,
                    "digest": "test-digest",
                },
            ))
            context_mock = stack.enter_context(patch.object(
                runner, "build_approved_context", side_effect=fake_context
            ))
            stack.enter_context(patch.object(
                runner.adapter, "post_json", side_effect=fake_render
            ))
            with redirect_stdout(io.StringIO()):
                if fail_render:
                    with self.assertRaisesRegex(
                        RuntimeError, "simulated rendering failure"
                    ):
                        runner.main()
                else:
                    runner.main()

        journals = list(output.glob("*.jsonl"))
        self.assertEqual(len(journals), 1)
        events = [
            json.loads(line)
            for line in journals[0].read_text(encoding="utf-8").splitlines()
        ]
        return output, events, render_count, context_mock.call_count

    def test_complete_preparation_skips_denied_and_no_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output, events, render_count, context_count = self.exercise(
                Path(directory)
            )
            reports = list(output.glob("*.json"))
            self.assertEqual(len(reports), 1)
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertEqual(len(report["cases"]), 8)
            self.assertEqual(context_count, 8)
            self.assertEqual(render_count, 6)
            self.assertIs(report["generation_performed"], False)
            self.assertEqual(report["execution_status"], "completed")
            self.assertEqual(
                [event["fields"]["record"] for event in events
                 if event["event_type"] == "case_prepared"],
                report["cases"],
            )
            for record in report["cases"][-2:]:
                self.assertIsNone(record["prepared"]["completion_request"])
                self.assertEqual(record["render_diagnostics"], [])
            self.assertEqual(
                events[-1]["event_type"], "preparation_completed"
            )

    def test_render_failure_preserves_prior_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            output, events, render_count, _ = self.exercise(
                Path(directory), fail_render=True
            )
            self.assertEqual(list(output.glob("*.json")), [])
            completed = [
                event for event in events
                if event["event_type"] == "case_prepared"
            ]
            self.assertEqual(len(completed), 1)
            self.assertEqual(
                completed[0]["fields"]["record"]["case"]["case_id"],
                "ROBUST-001",
            )
            self.assertEqual(render_count, 2)
            self.assertEqual(
                events[-1]["event_type"], "preparation_interrupted"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)