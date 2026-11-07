"""Run the permission-aware RAG baseline without a live model."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]

CHECKS = (
    "test_retrieve_documents.py",
    "test_document_context.py",
    "test_answer_boundary.py",
    "test_document_lifecycle.py",
    "test_provider_abstention.py",
    "test_evaluate_property_answers.py",
)


def main():
    results = []

    for filename in CHECKS:
        print(f"\nRunning {filename}", flush=True)

        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / filename)],
            cwd=ROOT,
            check=False,
        )

        results.append((filename, completed.returncode))

    print("\nBaseline summary")
    print("-" * 65)

    for filename, exit_code in results:
        status = "PASS" if exit_code == 0 else "FAIL"
        print(f"{status:4}  {filename}  (exit code: {exit_code})")

    failed = sum(exit_code != 0 for _, exit_code in results)

    print(f"\nScripts: {len(results)}; passed: {len(results) - failed}; failed: {failed}")
    print("Scope: local boundary checks; no live model quality measurement.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
