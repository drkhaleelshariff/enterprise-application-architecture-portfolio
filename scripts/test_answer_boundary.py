"""Verify generation gating and provider-response boundaries."""

import json
from unittest.mock import Mock

from answer_property_question import (
    ProviderUnavailable,
    answer_question,
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    query = "maintenance acknowledgement"

    provider = Mock(return_value={
        "answer": "The target acknowledgement time is two business days.",
        "citations": ["DOC-N-001:v1"],
    })

    result = answer_question("USR-001", query, provider)
    require(
        result == {
            "status": "answered",
            "answer": "The target acknowledgement time is two business days.",
            "citations": ["DOC-N-001:v1"],
        },
        "Expected the test provider response",
    )
    provider.assert_called_once()
    sent_query, context = provider.call_args.args
    require(sent_query == query, "Provider received the wrong query")
    sources = json.loads(context)["sources"]
    require(
        [source["citation"] for source in sources] == ["DOC-N-001:v1"],
        "Unauthorized source entered provider context",
    )
    print("PASS: provider receives only authorized North context")

    for identity_id in ["USR-004", "USR-005", "USR-999"]:
        blocked = Mock(side_effect=AssertionError("Provider must not run"))
        result = answer_question(identity_id, query, blocked)
        blocked.assert_not_called()
        require(
            result == {
                "status": "denied",
                "answer": "",
                "citations": [],
            },
            "Denied request returned answer content",
        )
        print(f"PASS: {identity_id} denied without provider invocation")

    blocked = Mock(side_effect=AssertionError("Provider must not run"))
    result = answer_question("USR-001", "astronomy", blocked)
    blocked.assert_not_called()
    require(
        result == {
            "status": "no_evidence",
            "answer": "No matching authorized evidence was found.",
            "citations": [],
        },
        "No-evidence response is incorrect",
    )
    print("PASS: no evidence skips provider invocation")

    for error in [
        ProviderUnavailable("Synthetic failure"),
        TimeoutError("Synthetic timeout"),
        ConnectionError("Synthetic connection failure"),
    ]:
        failed = Mock(side_effect=error)
        result = answer_question("USR-001", query, failed)
        failed.assert_called_once()
        require(
            result == {
                "status": "unavailable",
                "answer": "",
                "citations": [],
            },
            "Provider failure returned an answer",
        )
        print(f"PASS: {type(error).__name__} returns unavailable")

    invalid_responses = [
        {
            "answer": "Unauthorized citation",
            "citations": ["DOC-S-001:v1"],
        },
        {
            "answer": "",
            "citations": ["DOC-N-001:v1"],
        },
        {
            "answer": "Missing citations",
            "citations": [],
        },
        {
            "answer": "Duplicate citations",
            "citations": ["DOC-N-001:v1", "DOC-N-001:v1"],
        },
        "not a structured response",
    ]

    for number, response in enumerate(invalid_responses, start=1):
        result = answer_question(
            "USR-001", query, Mock(return_value=response)
        )
        require(
            result == {
                "status": "invalid_provider_response",
                "answer": "",
                "citations": [],
            },
            f"Invalid response {number} was accepted",
        )
        print(f"PASS: invalid provider response {number} is suppressed")

    print("\nResults: 13 passed; 0 failed")


if __name__ == "__main__":
    main()