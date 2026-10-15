"""Control access to an answer provider using authorized document context."""

from build_document_context import build_context
from retrieve_documents import DOCUMENT_DATA, IDENTITY_DATA


class ProviderUnavailable(RuntimeError):
    """The configured answer provider could not complete the request."""


def answer_question(
    identity_id,
    query,
    provider,
    identity_folder=IDENTITY_DATA,
    document_folder=DOCUMENT_DATA,
    *,
    context_builder=build_context,
):
    try:
        evidence = context_builder(
            identity_id,
            query,
            identity_folder=identity_folder,
            document_folder=document_folder,
        )
    except (OSError, ValueError, RecursionError):
        return {
            "status": "unavailable",
            "answer": "",
            "citations": [],
        }

    if evidence["decision"] != "allow":
        return {
            "status": "denied",
            "answer": "",
            "citations": [],
        }

    if evidence["context_status"] == "no_evidence":
        return {
            "status": "no_evidence",
            "answer": "No matching authorized evidence was found.",
            "citations": [],
        }

    try:
        result = provider(query, evidence["context"])
    except (ProviderUnavailable, TimeoutError, ConnectionError):
        return {
            "status": "unavailable",
            "answer": "",
            "citations": [],
        }

    # Accept only the exact abstention shape.
    if (
        isinstance(result, dict)
        and set(result) == {"status", "answer", "citations"}
        and result["status"] == "abstain"
        and result["answer"] == ""
        and result["citations"] == []
    ):
        return {
            "status": "abstained",
            "answer": "The supplied authorized evidence does not establish an answer.",
            "citations": [],
        }

    allowed_citations = {
        source["citation"] for source in evidence["sources"]
    }
    
    if (
        not isinstance(result, dict)
        or set(result) != {"answer", "citations"}
        or not isinstance(result["answer"], str)
        or not result["answer"].strip()
        or not isinstance(result["citations"], list)
        or not result["citations"]
        or any(
            not isinstance(citation, str)
            or citation not in allowed_citations
            for citation in result["citations"]
        )
        or len(result["citations"]) != len(set(result["citations"]))
    ):
        return {
            "status": "invalid_provider_response",
            "answer": "",
            "citations": [],
        }

    return {
        "status": "answered",
        "answer": result["answer"],
        "citations": result["citations"],
    }