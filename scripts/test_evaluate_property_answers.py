"""Verify evaluation recording using a mock provider, not a real model."""

from unittest.mock import Mock

from evaluate_property_answers import evaluate


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    provider = Mock(return_value={
        "status": "abstain",
        "answer": "",
        "citations": [],
    })

    report = evaluate(
        provider,
        provider_id="mock-abstention-provider",
        provider_configuration={"mode": "test"},
        prompt_version="mock-test-v1",
    )
    rows = {row["case_id"]: row for row in report["cases"]}

    require(
        report["case_count"] == 8
        and len(rows) == 8
        and report["review_status"] == "not_reviewed"
        and all(
            row["review"] == {
                "decision": "not_assessed",
                "explanation": "",
            }
            for row in rows.values()
        ),
        "Cases must remain explicitly unreviewed",
    )
    print("PASS: eight cases recorded without quality pass claims")

    require(
        report["provider_id"] == "mock-abstention-provider"
        and report["provider_configuration"] == {"mode": "test"}
        and report["prompt_version"] == "mock-test-v1"
        and bool(report["repository_commit"])
        and bool(report["recorded_at"]),
        "Run metadata is incomplete",
    )
    print("PASS: provider, prompt and repository metadata recorded")

    for case_id in ("EVAL-007", "EVAL-008"):
        row = rows[case_id]
        require(
            not row["provider_called"]
            and row["provider_call_count"] == 0
            and row["provider_calls"] == []
            and row["response"] == {
                "status": "denied",
                "answer": "",
                "citations": [],
            },
            f"{case_id}: denial invoked the provider or exposed content",
        )
    require(provider.call_count == 6, "Expected six provider calls")
    print("PASS: both denial cases skip the provider")

    for case_id in ("EVAL-001", "EVAL-003", "EVAL-004", "EVAL-005"):
        calls = rows[case_id]["provider_calls"]
        require(
            len(calls) == 1
            and calls[0]["sources"] == [{
                "document_id": "DOC-N-001",
                "version": "1",
                "citation": "DOC-N-001:v1",
            }],
            f"{case_id}: unexpected North evidence",
        )
    print("PASS: North cases record only authorized North evidence")

    south_sources = rows["EVAL-002"]["provider_calls"][0]["sources"]
    group_sources = rows["EVAL-006"]["provider_calls"][0]["sources"]

    require(
        south_sources == [{
            "document_id": "DOC-S-001",
            "version": "1",
            "citation": "DOC-S-001:v1",
        }]
        and {
            source["citation"] for source in group_sources
        } == {"DOC-N-001:v1", "DOC-S-001:v1"},
        "South or group evidence scope is incorrect",
    )
    print("PASS: South and group cases retain correct source versions")

    require(
        all(
            row["response"]["status"] == "abstained"
            and row["response"]["citations"] == []
            for row in rows.values()
            if row["provider_called"]
        )
        and all(
            row["duration_seconds"] >= 0
            for row in rows.values()
        )
        and rows["EVAL-001"]["expected_behavior"] == "answer"
        and rows["EVAL-001"]["required_facts"] == ["two business days"],
        "Responses, timing or evaluation expectations were changed",
    )
    print("PASS: responses and timing recorded without changing expectations")

    print("\nResults: 6 passed; 0 failed")


if __name__ == "__main__":
    main()