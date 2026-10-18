"""Test runner launch controls without starting a model."""

import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import launch_direct_property_runner as launcher


class LauncherTests(unittest.TestCase):
    def paths(self, root):
        executable = root / "runner.exe"
        model = root / "model.gguf"
        executable.write_bytes(b"synthetic executable")
        model.write_bytes(b"synthetic model")
        return executable, model, root / "runs"

    def child(self):
        child = Mock()
        child.pid = 12345
        child.wait.return_value = 0
        child.poll.return_value = 0
        child.returncode = 0
        return child

    def test_occupied_port_prevents_process_and_log_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            executable, model, base = self.paths(Path(directory))
            with patch.object(
                launcher, "require_free_port",
                side_effect=OSError("address in use"),
            ), patch.object(launcher.subprocess, "Popen") as start:
                with self.assertRaises(OSError):
                    launcher.launch(executable, model, base)
            start.assert_not_called()
            self.assertEqual(list(base.iterdir()), [])

    def test_existing_lock_prevents_launch_and_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            executable, model, base = self.paths(Path(directory))
            lock = base / f"port-{launcher.PORT}.lock"
            lock.mkdir(parents=True)
            with patch.object(
                launcher, "require_free_port"
            ) as check, patch.object(
                launcher.subprocess, "Popen"
            ) as start:
                with self.assertRaisesRegex(RuntimeError, "Launch lock exists"):
                    launcher.launch(executable, model, base)
            check.assert_not_called()
            start.assert_not_called()
            self.assertTrue(lock.is_dir())

    def test_sequential_launches_use_distinct_logs_and_record_processes(self):
        with tempfile.TemporaryDirectory() as directory:
            executable, model, base = self.paths(Path(directory))
            with patch.object(
                launcher, "require_free_port"
            ), patch.object(
                launcher.subprocess, "Popen",
                side_effect=[self.child(), self.child()],
            ) as start, redirect_stdout(io.StringIO()):
                self.assertEqual(launcher.launch(executable, model, base), 0)
                self.assertEqual(launcher.launch(executable, model, base), 0)

            folders = sorted(base.glob("run-*"))
            self.assertEqual(len(folders), 2)
            logs = []
            for folder in folders:
                record = json.loads(
                    (folder / "launch.json").read_text(encoding="utf-8")
                )
                logs.append(record["log_file"])
                self.assertEqual(
                    record["executable_sha256"],
                    hashlib.sha256(executable.read_bytes()).hexdigest(),
                )
                self.assertIs(record["health_verified"], False)
                self.assertIs(record["port_bind_check_passed"], True)
                started = json.loads(
                    (folder / "process-started.json").read_text(
                        encoding="utf-8"
                    )
                )
                finished = json.loads(
                    (folder / "process-finished.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(started["runner_pid"], 12345)
                self.assertEqual(finished["returncode"], 0)
                self.assertIs(finished["launcher_interrupted"], False)

            self.assertEqual(len(set(logs)), 2)
            for call, log in zip(start.call_args_list, logs):
                # Directory sorting need not match launch order.
                self.assertIn(
                    call.args[0][call.args[0].index("--log-file") + 1],
                    logs,
                )
                self.assertIs(call.kwargs["shell"], False)
            self.assertFalse((base / f"port-{launcher.PORT}.lock").exists())

    def test_failed_process_start_preserves_launch_record_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            executable, model, base = self.paths(Path(directory))
            with patch.object(
                launcher, "require_free_port"
            ), patch.object(
                launcher.subprocess, "Popen",
                side_effect=OSError("cannot start"),
            ), redirect_stdout(io.StringIO()):
                with self.assertRaises(OSError):
                    launcher.launch(executable, model, base)
            folder = next(base.glob("run-*"))
            self.assertTrue((folder / "launch.json").exists())
            self.assertFalse((folder / "process-started.json").exists())
            self.assertFalse((base / f"port-{launcher.PORT}.lock").exists())

    def test_keyboard_interrupt_terminates_owned_child(self):
        with tempfile.TemporaryDirectory() as directory:
            executable, model, base = self.paths(Path(directory))
            child = self.child()
            child.wait.side_effect = [KeyboardInterrupt(), -15]
            child.poll.side_effect = [None, -15, -15]
            child.returncode = -15
            with patch.object(
                launcher, "require_free_port"
            ), patch.object(
                launcher.subprocess, "Popen", return_value=child
            ), redirect_stdout(io.StringIO()):
                self.assertEqual(
                    launcher.launch(executable, model, base), -15
                )
            child.terminate.assert_called_once()
            child.kill.assert_not_called()
            folder = next(base.glob("run-*"))
            finished = json.loads(
                (folder / "process-finished.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIs(finished["launcher_interrupted"], True)
            self.assertFalse((base / f"port-{launcher.PORT}.lock").exists())

    def test_recording_failure_cleans_up_owned_child(self):
        with tempfile.TemporaryDirectory() as directory:
            executable, model, base = self.paths(Path(directory))
            child = self.child()
            child.poll.side_effect = [None, -15]
            child.returncode = -15
            original = launcher.write_record

            def fail_started(path, record):
                if path.name == "process-started.json":
                    raise OSError("recording failed")
                return original(path, record)

            with patch.object(
                launcher, "require_free_port"
            ), patch.object(
                launcher.subprocess, "Popen", return_value=child
            ), patch.object(
                launcher, "write_record", side_effect=fail_started
            ), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(OSError, "recording failed"):
                    launcher.launch(executable, model, base)
            child.terminate.assert_called_once()
            self.assertFalse((base / f"port-{launcher.PORT}.lock").exists())

    def test_existing_records_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            launcher.write_record(path, {"original": True})
            before = path.read_bytes()
            with self.assertRaises(FileExistsError):
                launcher.write_record(path, {"replacement": True})
            self.assertEqual(path.read_bytes(), before)

    def test_command_retains_cpu_and_context_controls(self):
        command = launcher.runner_command(
            Path("runner.exe"), Path("model.gguf"), Path("unique.log")
        )
        for flag, value in {
            "--host": "127.0.0.1",
            "--port": "18081",
            "-ngl": "0",
            "-np": "1",
            "-c": "4096",
            "-b": "512",
            "-ub": "512",
            "--log-file": "unique.log",
        }.items():
            self.assertEqual(command[command.index(flag) + 1], value)


if __name__ == "__main__":
    unittest.main(verbosity=2)