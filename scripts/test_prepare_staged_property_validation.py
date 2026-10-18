"""Test twelve-case preparation without contacting model services."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import prepare_staged_property_validation as runner


def context_for(status):
    sources = [] if status == "denied" else [{
        "citation": "DOC-N-VISITOR-001:v1",
        "document_id": "DOC-N-VISITOR-001",
        "version": "1",
        "title": "Synthetic visitor policy",
        "text": "Synthetic visitor policy text.",
    }]
    return {
        "decision": "deny" if status == "denied" else "allow",
        "context_status": status,
        "sources": sources,
        "context": json.dumps({"sources": sources}) if sources else "",
    }


class ValidationPreparationTests(unittest.TestCase):
    def exercise(self, root, *, fail_render=False, reverse_cases=False):
        fixtures = root / "data"
        fixtures.mkdir()
        output = root / "evidence"
        cases = [
            {
                "case_id": f"STVAL-{number:03d}",
                "identity_id": "SYNTHETIC",
                "question": f"Question {number}",
                "expected_behavior": "deny" if number == 11 else "answer",
                "required_facts": [],
                "required_citations": [],
                "review_note": "Mocked preparation test",
            }
            for number in range(1, 13)
        ]
        if reverse_cases:
            cases.reverse()

        (fixtures / "cases.json").write_text(
            json.dumps({"schema_version": "1", "cases": cases}),
            encoding="utf-8",
        )
        (fixtures / "documents.json").write_text(
            '{"schema_version":"1","documents":[]}\n',
            encoding="utf-8",
        )
        (fixtures / "source_approvals.json").write_text(
            '{"schema_version":"1","approved_sources":[]}\n',
            encoding="utf-8",
        )
        (fixtures / "plan.md").write_text(
            "# Synthetic test plan\n", encoding="utf-8"
        )
        hashes = {
            name: hashlib.sha256((fixtures / name).read_bytes()).hexdigest()
            for name in (
                "plan.md", "cases.json", "documents.json",
                "source_approvals.json",
            )
        }

        def fake_context(identity, query, **kwargs):
            self.assertEqual(identity, "SYNTHETIC")
            self.assertEqual(kwargs["document_folder"], fixtures)
            self.assertEqual(
                kwargs["approval_path"], fixtures / "source_approvals.json"
            )
            number = int(query.split()[-1])
            return context_for("denied" if number == 11 else "ready")

        render_count = 0

        def fake_render(port, path, payload, stage, diagnostics):
            nonlocal render_count
            render_count += 1
            self.assertEqual(
                (port, path, stage), (11434, "/api/generate", "render")
            )
            self.assertIs(payload["_debug_render_only"], True)
            self.assertIs(payload["stream"], False)
            if fail_render and render_count == 2:
                raise RuntimeError("simulated rendering failure")
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
            service = stack.enter_context(patch.object(
                runner, "get_json", return_value={"version": "test"}
            ))
            metadata = stack.enter_context(patch.object(
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
                if reverse_cases:
                    with self.assertRaisesRegex(
                        ValueError, "Expected STVAL-001"
                    ):
                        runner.main()
                elif fail_render:
                    with self.assertRaisesRegex(
                        RuntimeError, "simulated rendering failure"
                    ):
                        runner.main()
                else:
                    runner.main()

        events = []
        journals = list(output.glob("*.jsonl"))
        if journals:
            self.assertEqual(len(journals), 1)
            events = [
                json.loads(line)
                for line in journals[0].read_text(
                    encoding="utf-8"
                ).splitlines()
            ]
        return {
            "output": output,
            "events": events,
            "render_count": render_count,
            "context_count": context_mock.call_count,
            "service_count": service.call_count,
            "metadata_count": metadata.call_count,
            "hashes": hashes,
        }

    def test_complete_preparation_records_hashes_and_skips_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.exercise(Path(directory))
            reports = list(result["output"].glob("*.json"))
            self.assertEqual(len(reports), 1)
            self.assertTrue(
                reports[0].name.startswith("staged-validation-preparation-")
            )
            report = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertEqual(
                report["suite_id"], "staged-visitor-permit-validation-v1"
            )
            self.assertEqual(report["fixture_sha256"], result["hashes"])
            self.assertEqual(len(report["cases"]), 12)
            self.assertEqual(result["context_count"], 12)
            self.assertEqual(result["render_count"], 11)
            self.assertIs(report["generation_performed"], False)
            self.assertEqual(report["execution_status"], "completed")
            self.assertEqual(
                [event["fields"]["record"] for event in result["events"]
                 if event["event_type"] == "case_prepared"],
                report["cases"],
            )
            for number, record in enumerate(report["cases"], start=1):
                payload = record["prepared"]["completion_request"]
                if number == 11:
                    self.assertIsNone(payload)
                    self.assertEqual(record["render_diagnostics"], [])
                else:
                    self.assertIsInstance(payload, dict)
                    self.assertIs(payload["cache_prompt"], False)
            self.assertEqual(
                result["events"][-1]["event_type"], "preparation_completed"
            )

    def test_render_failure_preserves_prior_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.exercise(Path(directory), fail_render=True)
            self.assertEqual(list(result["output"].glob("*.json")), [])
            completed = [
                event for event in result["events"]
                if event["event_type"] == "case_prepared"
            ]
            self.assertEqual(len(completed), 1)
            self.assertEqual(
                completed[0]["fields"]["record"]["case"]["case_id"],
                "STVAL-001",
            )
            self.assertEqual(result["render_count"], 2)
            self.assertEqual(
                result["events"][-1]["event_type"],
                "preparation_interrupted",
            )

    def test_changed_case_order_prevents_service_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.exercise(Path(directory), reverse_cases=True)
            self.assertEqual(result["render_count"], 0)
            self.assertEqual(result["context_count"], 0)
            self.assertEqual(result["service_count"], 0)
            self.assertEqual(result["metadata_count"], 0)
            self.assertFalse(result["output"].exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)