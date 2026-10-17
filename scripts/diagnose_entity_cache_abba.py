"""Run four fresh direct-runner sequences in predefined ABBA order."""

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from evaluate_property_answers import ROOT, repository_commit
from run_property_evaluation import OUTPUT

PLAN = ("cache_on", "cache_off", "cache_off", "cache_on")
PREPARATION = (
    "projects/05-permission-aware-rag/evidence/"
    "entity-cache-control-preparation-20261017T084917606456Z.json"
)
MODEL_BLOB = (
    "sha256-dec52a44569a2a25341c4e4d3fee25846eed4f6f0b936278e3a3c900bb99d37c"
)


def port_open():
    with socket.socket() as connection:
        connection.settimeout(1)
        return connection.connect_ex(("127.0.0.1", 18081)) == 0


def wait_ready(process):
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Runner exited before becoming ready")
        try:
            with urlopen("http://127.0.0.1:18081/health", timeout=2) as response:
                if json.load(response).get("status") == "ok":
                    return
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    raise TimeoutError("Runner did not become ready within 180 seconds")


def stop_runner(process, record):
    record["process_alive_before_shutdown"] = process.poll() is None
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            record["forced_kill_required"] = True
            process.kill()
            process.wait(timeout=10)
    record["process_returncode"] = process.returncode
    record["process_exit_verified"] = process.poll() is not None

    deadline = time.monotonic() + 10
    while port_open() and time.monotonic() < deadline:
        time.sleep(0.25)
    record["port_closed_after_shutdown"] = not port_open()


def main():
    changes = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    if changes.stdout.strip():
        raise RuntimeError("Commit working-tree changes before execution")
    if port_open():
        raise RuntimeError("Port 18081 is occupied; no process was stopped")

    executable = (
        Path(os.environ["LOCALAPPDATA"])
        / "Programs/Ollama/lib/ollama/llama-server.exe"
    )
    model = Path.home() / ".ollama/models/blobs" / MODEL_BLOB
    if not executable.is_file() or not model.is_file():
        raise FileNotFoundError("Expected runner or model blob is missing")

    preparation_path = ROOT / PREPARATION
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT / f"entity-cache-abba-{stamp}.json"
    report = {
        "experiment": "fresh-process-direct-entity-cache-abba",
        "repository_commit": repository_commit(),
        "planned_conditions": list(PLAN),
        "planned_generation_calls": 8,
        "automatic_retries": 0,
        "runner_path": str(executable),
        "runner_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "model_blob_path": str(model),
        "preparation_file": PREPARATION,
        "preparation_sha256": hashlib.sha256(
            preparation_path.read_bytes()
        ).hexdigest(),
        "review_status": "not_reviewed",
        "execution_status": "running",
        "sequences": [],
    }

    try:
        for number, condition in enumerate(PLAN, start=1):
            if port_open():
                raise RuntimeError("Port occupied before fresh sequence")

            record = {
                "sequence": number,
                "condition": condition,
                "port_closed_before_start": True,
            }
            report["sequences"].append(record)
            prefix = f"entity-cache-abba-{stamp}-{number}-{condition}"
            log_path = OUTPUT / f"{prefix}-runner.txt"
            client_path = OUTPUT / f"{prefix}-client.txt"

            command = [
                str(executable),
                "--model", str(model),
                "--port", "18081",
                "--host", "127.0.0.1",
                "--no-webui", "--offline",
                "-c", "4096", "-np", "1",
                "--log-verbosity", "4",
                "--no-log-prefix", "--no-log-timestamps",
                "--no-jinja", "--chat-template", "chatml",
                "--mmproj", str(model), "--no-mmproj-offload",
                "--load-mode", "none", "--flash-attn", "auto",
                "-b", "512", "-ub", "512", "-ngl", "0",
                "--context-shift", "--keep", "4",
            ]
            record["command"] = command
            record["runner_log"] = log_path.relative_to(ROOT).as_posix()
            record["client_output"] = client_path.relative_to(ROOT).as_posix()

            print(f"Sequence {number}/4: {condition}", flush=True)
            before = set(OUTPUT.glob(f"direct-entity-cache-{condition}-*.json"))

            with log_path.open("xb") as log:
                process = subprocess.Popen(
                    command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                )
                record["pid"] = process.pid
                record["started_at"] = datetime.now(timezone.utc).isoformat()
                try:
                    wait_ready(process)
                    record["health_verified"] = True
                    with client_path.open("xb") as client:
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(ROOT / "scripts/diagnose_direct_entity_cache.py"),
                                PREPARATION,
                                condition,
                            ],
                            cwd=ROOT,
                            stdout=client,
                            stderr=subprocess.STDOUT,
                            timeout=420,
                        )
                    record["client_returncode"] = result.returncode

                    created = set(
                        OUTPUT.glob(f"direct-entity-cache-{condition}-*.json")
                    ) - before
                    record["created_run_files"] = [
                        p.relative_to(ROOT).as_posix() for p in sorted(created)
                    ]
                    if result.returncode != 0 or len(created) != 1:
                        raise RuntimeError("Client failed or run-file count differs")

                    run_path = created.pop()
                    run = json.loads(run_path.read_text(encoding="utf-8"))
                    record["outcomes"] = [
                        {
                            "case_id": request["case"]["case_id"],
                            "response": request.get("response"),
                        }
                        for request in run["requests"]
                    ]
                    print(json.dumps(record["outcomes"], indent=2), flush=True)
                finally:
                    stop_runner(process, record)

            if not record["port_closed_after_shutdown"]:
                raise RuntimeError("Runner port remained occupied")

        report["execution_status"] = "completed"
    except Exception as exc:
        report["execution_status"] = "interrupted"
        report["experiment_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        raise
    finally:
        report["recorded_at"] = datetime.now(timezone.utc).isoformat()
        with report_path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Saved: {report_path}", flush=True)


if __name__ == "__main__":
    main()