"""Verify cited context and empty-context boundaries."""

import json

from build_document_context import build_context


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    north = build_context("USR-001", "maintenance acknowledgement")
    require(
        north["decision"] == "allow"
        and north["context_status"] == "ready"
        and [s["citation"] for s in north["sources"]] == ["DOC-N-001:v1"],
        "Incorrect North context",
    )
    require(
        json.loads(north["context"]) == {"sources": north["sources"]},
        "Serialized context differs from source records",
    )
    require(
        "DOC-S-001" not in north["context"]
        and "South Retail" not in north["context"],
        "South information entered North context",
    )
    print("PASS: North context contains only its versioned source")

    south = build_context("USR-002", "maintenance acknowledgement")
    require(
        [s["citation"] for s in south["sources"]] == ["DOC-S-001:v1"]
        and "DOC-N-001" not in south["context"],
        "Incorrect South context",
    )
    print("PASS: South context excludes North information")

    group = build_context("USR-003", "maintenance acknowledgement")
    require(
        {s["citation"] for s in group["sources"]}
        == {"DOC-N-001:v1", "DOC-S-001:v1"},
        "Group context must include both authorized sources",
    )
    print("PASS: group context contains both authorized citations")

    empty = build_context("USR-001", "astronomy")
    require(
        empty == {
            "decision": "allow",
            "context_status": "no_evidence",
            "sources": [],
            "context": "",
        },
        "No-evidence result contains context",
    )
    print("PASS: no evidence produces empty context")

    for identity_id in ["USR-004", "USR-005", "USR-999"]:
        denied = build_context(identity_id, "maintenance acknowledgement")
        require(
            denied == {
                "decision": "deny",
                "context_status": "denied",
                "sources": [],
                "context": "",
            },
            f"Denied identity received context: {identity_id}",
        )
        print(f"PASS: {identity_id} receives no context or citations")

    print("\nResults: 7 passed; 0 failed")


if __name__ == "__main__":
    main()