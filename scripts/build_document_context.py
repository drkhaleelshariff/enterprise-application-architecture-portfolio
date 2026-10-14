"""Build cited context from permission-filtered retrieval."""

import argparse
import json

from retrieve_documents import (
    DOCUMENT_DATA,
    IDENTITY_DATA,
    retrieve,
)


def build_context(
    identity_id,
    query,
    identity_folder=IDENTITY_DATA,
    document_folder=DOCUMENT_DATA,
):
    result = retrieve(
        identity_id,
        query,
        identity_folder=identity_folder,
        document_folder=document_folder,
    )

    if result["decision"] != "allow":
        return {
            "decision": "deny",
            "context_status": "denied",
            "sources": [],
            "context": "",
        }

    if not result["matches"]:
        return {
            "decision": "allow",
            "context_status": "no_evidence",
            "sources": [],
            "context": "",
        }

    sources = []
    for match in result["matches"]:
        sources.append({
            "citation": (
                f"{match['document_id']}:v{match['version']}"
            ),
            "document_id": match["document_id"],
            "version": match["version"],
            "title": match["title"],
            "text": match["text"],
        })

    # Structured JSON preserves source fields without relying on
    # document text to supply its own citation labels.
    context = json.dumps(
        {"sources": sources},
        ensure_ascii=False,
        indent=2,
    )

    return {
        "decision": "allow",
        "context_status": "ready",
        "sources": sources,
        "context": context,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build authorized cited document context"
    )
    parser.add_argument("identity_id")
    parser.add_argument("query")
    args = parser.parse_args()

    try:
        result = build_context(args.identity_id, args.query)
    except (OSError, ValueError, RecursionError):
        print(json.dumps({
            "decision": "deny",
            "context_status": "unavailable",
            "sources": [],
            "context": "",
        }, indent=2))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"] == "allow" else 1


if __name__ == "__main__":
    raise SystemExit(main())