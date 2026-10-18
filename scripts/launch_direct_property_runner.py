"""Launch one local CPU runner with a unique log and launch record."""

import hashlib
import json
import os
import socket
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


MODEL_BLOB = (
    "sha256-dec52a44569a2a25341c4e4d3fee25846eed4f6f0b"
    "936278e3a3c900bb99d37c"
)
PORT = 18081


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def require_free_port(port):
    # This check does not reserve the port until the child binds it.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(("127.0.0.1", port))


def runner_command(executable, model, log):
    return [
        str(executable),
        "--model", str(model),
        "--port", str(PORT),
        "--host", "127.0.0.1",
        "--no-webui", "--offline",
        "-c", "4096", "-np", "1",
        "--log-verbosity", "4",
        "--no-log-prefix", "--no-log-timestamps",
        "--no-jinja", "--chat-template", "chatml",
        "--mmproj", str(model),
        "--no-mmproj-offload",
        "--load-mode", "none",
        "--flash-attn", "auto",
        "-b", "512", "-ub", "512",
        "-ngl", "0",
        "--context-shift", "--keep", "4",
        "--log-file", str(log),
    ]


def write_record(path, record):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")


def launch(executable, model, base):
    executable = Path(executable).resolve()
    model = Path(model).resolve()
    base = Path(base).resolve()

    for path in (executable, model):
        if not path.is_file():
            raise FileNotFoundError(path)

    base.mkdir(parents=True, exist_ok=True)
    lock = base / f"port-{PORT}.lock"

    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise RuntimeError(
            f"Launch lock exists: {lock}. "
            "Check existing launcher and runner processes before recovery."
        ) from exc

    child = None
    run_folder = None
    try:
        require_free_port(PORT)
        run_folder = Path(tempfile.mkdtemp(prefix="run-", dir=base))
        log = run_folder / "runner.log"
        command = runner_command(executable, model, log)
        write_record(run_folder / "launch.json", {
            "recorded_at": utc_now(),
            "launcher_pid": os.getpid(),
            "executable": str(executable),
            "executable_sha256": hashlib.sha256(
                executable.read_bytes()
            ).hexdigest(),
            "model_path": str(model),
            "command": command,
            "log_file": str(log),
            "port": PORT,
            "port_bind_check_passed": True,
            "health_verified": False,
        })

        print(f"Run directory: {run_folder}", flush=True)
        print("Keep this window open. Ctrl+C stops its runner.", flush=True)
        child = subprocess.Popen(command, shell=False)
        write_record(run_folder / "process-started.json", {
            "recorded_at": utc_now(),
            "runner_pid": child.pid,
        })
        print(f"Runner PID: {child.pid}", flush=True)
        print("Verify /health from another window before evaluation.", flush=True)

        interrupted = False
        try:
            returncode = child.wait()
        except KeyboardInterrupt:
            interrupted = True
            returncode = None
        finally:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            returncode = child.returncode

        write_record(run_folder / "process-finished.json", {
            "recorded_at": utc_now(),
            "runner_pid": child.pid,
            "returncode": returncode,
            "launcher_interrupted": interrupted,
        })
        return returncode
    finally:
        # Also clean up our child if recording or another operation fails.
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

        if child is None or child.poll() is not None:
            lock.rmdir()


def main():
    executable = (
        Path(os.environ["LOCALAPPDATA"])
        / "Programs" / "Ollama" / "lib" / "ollama" / "llama-server.exe"
    )
    model = Path.home() / ".ollama" / "models" / "blobs" / MODEL_BLOB
    base = Path(tempfile.gettempdir()) / "property-direct-runner"
    return launch(executable, model, base)


if __name__ == "__main__":
    raise SystemExit(main())