"""Build policy-answer context from authorized, approved source versions."""

import json
import re
from pathlib import Path

from retrieve_documents import (
    IDENTITY_DATA,
    load_data,
    load_documents,
    rank_documents,
)
from source_approvals import load_approvals


def build_approved_context(
    identity_id,
    query,
    *,
    document_folder,
    approval_path,
    identity_folder=IDENTITY_DATA,
):
    if (
        not isinstance(query, str)
        or not query.strip()
        or len(query) > 1000
    ):
        raise ValueError("Query must contain 1 to 1000 characters")

    identities, roles, _ = load_data(identity_folder)
    identity = identities.get(identity_id)

    if (
        identity is None
        or identity["status"] != "active"
        or "document:read"
        not in roles[identity["role"]]["allowed_actions"]
    ):
        return {
            "decision": "deny",
            "context_status": "denied",
            "sources": [],
            "context": "",
        }

    documents = load_documents(Path(document_folder))
    approved = load_approvals(approval_path)

    authorized = [
        document
        for document in documents
        if document["status"] == "active"
        and document["entity_id"] in identity["entity_ids"]
    ]

    eligible = [
        document
        for document in authorized
        if (document["document_id"], document["version"]) in approved
    ]

    # Neither unauthorized nor unapproved text reaches ranking.
    matches = rank_documents(query, eligible)

    if not matches:
        return {
            "decision": "allow",
            "context_status": "no_evidence",
            "sources": [],
            "context": "",
        }

    sources = [
        {
            "citation": (
                f"{match['document_id']}:v{match['version']}"
            ),
            "document_id": match["document_id"],
            "version": match["version"],
            "title": match["title"],
            "text": match["text"],
        }
        for match in matches
    ]

    return {
        "decision": "allow",
        "context_status": "ready",
        "sources": sources,
        "context": json.dumps(
            {"sources": sources},
            ensure_ascii=False,
            indent=2,
        ),
    }