"""Record one direct-runner predecessor sequence with explicit caching."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from answer_approved_property_question import answer_approved_question
from answer_property_question import ProviderUnavailable
from diagnose_entity_predecessor import FIXTURES, APPROVALS
from evaluate_property_answers import ROOT, repository_commit
from ollama_schema_property_provider import unique_object
from run_property_evaluation import OUTPUT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("preparation", type=str)
    parser.add_argument("condition", choices=["cache_on", "cache_off"])
    args = parser.parse_args()

    preparation_path = ROOT / args.preparation
    preparation_bytes = preparation_path.read_bytes()
    preparation = json.loads(preparation_bytes)
    report = {
        "experiment": "direct-entity-cache-control",
        "repository_commit": repository_commit(),
        "condition": args.condition,
        "endpoint": "http://127.0.0.1:18081/completion",
        "preparation_file": args.preparation,
        "preparation_sha256": hashlib.sha256(preparation_bytes).hexdigest(),
        "fresh_runner": "operator_supplied; not independently verified",
        "automatic_retries": 0,
        "review_status": "not_reviewed",
        "requests": [],
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path = OUTPUT / f"direct-entity-cache-{args.condition}-{stamp}.json"

    try:
        for prepared in preparation["cases"]:
            case = prepared["case"]
            payload = prepared["direct_completion_requests"][args.condition]
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            record = {
                "case": case,
                "request_body_utf8": body.decode("utf-8"),
                "request_body_sha256": hashlib.sha256(body).hexdigest(),
                "provider_call_count": 0,
            }
            report["requests"].append(record)

            def direct_provider(query, context):
                if query != case["question"]:
                    raise RuntimeError("Question differs from preparation")
                if json.loads(context) != prepared["authorized_evidence"]:
                    raise RuntimeError("Evidence differs from preparation")

                record["provider_call_count"] += 1
                request = Request(
                    report["endpoint"],
                    data=body,
                    headers={"Content-Type": "application/json"},
                )
                try:
                    with urlopen(request, timeout=180) as response:
                        raw = response.read(1_048_577)
                        record["http_status"] = response.status
                except HTTPError as exc:
                    record["http_status"] = exc.code
                    record["error_body"] = exc.read(4096).decode(
                        "utf-8", errors="replace"
                    )
                    raise ProviderUnavailable("Direct runner HTTP failure") from exc
                except (URLError, OSError) as exc:
                    record["transport_error"] = {
                        "type": type(exc).__name__,
                        "message": str(exc),
                    }
                    raise ProviderUnavailable("Direct runner unavailable") from exc

                record["raw_response"] = raw.decode("utf-8", errors="replace")
                if len(raw) > 1_048_576:
                    raise ProviderUnavailable("Direct response exceeded limit")

                try:
                    envelope = json.loads(raw, object_pairs_hook=unique_object)
                    record["runner_response"] = envelope
                    if envelope.get("truncated") or envelope.get("stopped_limit"):
                        return {}
                    content = envelope["content"]
                    return json.loads(content, object_pairs_hook=unique_object)
                except (ValueError, KeyError, TypeError, AttributeError):
                    return {}

            print(f"Running {case['case_id']} ({args.condition})...", flush=True)
            started = perf_counter()
            record["response"] = answer_approved_question(
                case["identity_id"],
                case["question"],
                direct_provider,
                document_folder=FIXTURES,
                approval_path=APPROVALS,
            )
            record["duration_seconds"] = round(perf_counter() - started, 6)
            print(json.dumps(record["response"], indent=2), flush=True)

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
        with path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Saved: {path}", flush=True)


if __name__ == "__main__":
    main()