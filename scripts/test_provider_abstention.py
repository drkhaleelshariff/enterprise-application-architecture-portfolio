"""Verify explicit provider abstention and malformed-response rejection."""

from unittest.mock import Mock

from answer_property_question import answer_question


def main():
    query = "How much compensation is paid for delayed maintenance?"

    provider = Mock(return_value={
        "status": "abstain",
        "answer": "",
        "citations": [],
    })

    result = answer_question("USR-001", query, provider)
    provider.assert_called_once()

    if result != {
        "status": "abstained",
        "answer": "The supplied authorized evidence does not establish an answer.",
        "citations": [],
    }:
        raise AssertionError(f"Unexpected abstention response: {result}")

    print("PASS: explicit abstention returns the application message")

    invalid_responses = [
        {
            "status": "abstain",
            "answer": "Unsupported provider explanation",
            "citations": [],
        },
        {
            "status": "abstain",
            "answer": "",
            "citations": ["DOC-N-001:v1"],
        },
        {
            "status": "abstain",
            "answer": "",
        },
        {
            "status": "abstain",
            "answer": "",
            "citations": [],
            "extra": "Unexpected field",
        },
    ]

    for number, response in enumerate(invalid_responses, start=1):
        provider = Mock(return_value=response)
        result = answer_question("USR-001", query, provider)
        provider.assert_called_once()

        if result != {
            "status": "invalid_provider_response",
            "answer": "",
            "citations": [],
        }:
            raise AssertionError(
                f"Malformed abstention {number} was accepted: {result}"
            )

        print(f"PASS: malformed abstention {number} is suppressed")

    print("\nResults: 5 passed; 0 failed")


if __name__ == "__main__":
    main()