"""Retrieve synthetic documents after permission and entity filtering."""

import argparse
import json
import re

from authorize_lease import DATA as IDENTITY_DATA
from authorize_lease import ENTITIES, ROOT, load_data, unique_object

DOCUMENT_DATA = ROOT / "projects" / "05-permission-aware-rag" / "data"


def load_documents(folder):
    with (folder / "documents.json").open(encoding="utf-8-sig") as handle:
        document = json.load(handle, object_pairs_hook=unique_object)

    if (
        not isinstance(document, dict)
        or set(document) != {"schema_version", "documents"}
        or document["schema_version"] != "1"
        or not isinstance(document["documents"], list)
    ):
        raise ValueError("Invalid document register")

    fields = {
        "document_id", "version", "entity_id",
        "title", "status", "text",
    }
    seen = set()
    records = []

    for row in document["documents"]:
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError("Invalid document fields")

        if any(
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
            for value in row.values()
        ):
            raise ValueError("Invalid document value")

        if (
            row["document_id"] in seen
            or row["entity_id"] not in ENTITIES
            or row["status"] not in {"active", "deleted"}
            or not re.fullmatch(r"[1-9][0-9]*", row["version"])
        ):
            raise ValueError("Invalid document metadata")

        seen.add(row["document_id"])
        records.append(row)

    return records


def rank_documents(query, documents):
    """Receive authorized documents only."""
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    matches = []

    for document in documents:
        words = set(re.findall(
            r"[a-z0-9]+",
            (document["title"] + " " + document["text"]).lower(),
        ))
        score = len(terms & words)
        if score:
            matches.append({
                "document_id": document["document_id"],
                "version": document["version"],
                "title": document["title"],
                "text": document["text"],
                "score": score,
            })

    return sorted(
        matches,
        key=lambda match: (-match["score"], match["document_id"]),
    )


def retrieve(
    identity_id,
    query,
    identity_folder=IDENTITY_DATA,
    document_folder=DOCUMENT_DATA,
):
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError("Query must contain 1 to 1000 characters")

    identities, roles, _ = load_data(identity_folder)
    identity = identities.get(identity_id)

    if (
        identity is None
        or identity["status"] != "active"
        or "document:read"
        not in roles[identity["role"]]["allowed_actions"]
    ):
        return {"decision": "deny", "matches": []}

    documents = load_documents(document_folder)

    # Authorization occurs before document text reaches the ranking function.
    authorized = [
        document
        for document in documents
        if document["status"] == "active"
        and document["entity_id"] in identity["entity_ids"]
    ]

    matches = rank_documents(query, authorized)
    return {
        "decision": "allow",
        "retrieval_status": "matched" if matches else "no_evidence",
        "matches": matches,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve authorized synthetic property documents"
    )
    parser.add_argument("identity_id")
    parser.add_argument("query")
    args = parser.parse_args()

    try:
        result = retrieve(args.identity_id, args.query)
    except (OSError, ValueError, RecursionError):
        print(json.dumps({
            "decision": "deny",
            "error": "invalid_input_or_unavailable_configuration",
            "matches": [],
        }, indent=2))
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["decision"] == "allow" else 1


if __name__ == "__main__":
    raise SystemExit(main())