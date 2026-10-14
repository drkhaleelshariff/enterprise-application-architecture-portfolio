"""Verify document and permission changes affect subsequent requests."""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

from answer_property_question import answer_question
from authorize_lease import DATA
from build_document_context import build_context
from retrieve_documents import DOCUMENT_DATA


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def save(path, document):
    path.write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )


def main():
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        identities = base / "identities"
        documents = base / "documents"
        shutil.copytree(DATA, identities)
        shutil.copytree(DOCUMENT_DATA, documents)

        query = "maintenance acknowledgement"

        def context():
            return build_context(
                "USR-001", query,
                identity_folder=identities,
                document_folder=documents,
            )

        def answer(provider):
            return answer_question(
                "USR-001", query, provider,
                identity_folder=identities,
                document_folder=documents,
            )

        baseline = context()
        require(
            [s["citation"] for s in baseline["sources"]]
            == ["DOC-N-001:v1"],
            "Expected baseline version 1",
        )
        print("PASS: baseline context uses version 1")

        path = documents / "documents.json"
        register = json.loads(path.read_text(encoding="utf-8-sig"))
        original = json.loads(json.dumps(register))

        for document in register["documents"]:
            if document["document_id"] == "DOC-N-001":
                document["version"] = "2"
                document["text"] = (
                    "North routine maintenance requests have a target "
                    "acknowledgement time of three business days."
                )
        save(path, register)

        updated = context()
        require(
            [s["citation"] for s in updated["sources"]]
            == ["DOC-N-001:v2"]
            and "three business days" in updated["context"]
            and "two business days" not in updated["context"],
            "Updated context retained stale text or citation",
        )
        print("PASS: next context reflects updated text and version")

        provider = Mock(return_value={
            "answer": "Synthetic test response.",
            "citations": ["DOC-N-001:v2"],
        })
        result = answer(provider)
        provider.assert_called_once()
        sent_context = provider.call_args.args[1]
        require(
            result["status"] == "answered"
            and "DOC-N-001:v2" in sent_context
            and "DOC-N-001:v1" not in sent_context,
            "Provider received stale evidence",
        )
        print("PASS: provider receives updated evidence only")

        stale = Mock(return_value={
            "answer": "Synthetic stale response.",
            "citations": ["DOC-N-001:v1"],
        })
        require(
            answer(stale)["status"] == "invalid_provider_response",
            "Stale citation was accepted",
        )
        print("PASS: citation to superseded version is rejected")

        for document in register["documents"]:
            if document["document_id"] == "DOC-N-001":
                document["status"] = "deleted"
        save(path, register)

        blocked = Mock(side_effect=AssertionError("Provider must not run"))
        result = answer(blocked)
        blocked.assert_not_called()
        require(
            result["status"] == "no_evidence"
            and result["citations"] == [],
            "Deleted evidence remained available",
        )
        print("PASS: deletion excludes evidence and skips provider")

        # Restore documents, then remove North membership.
        save(path, original)
        identity_path = identities / "identities.json"
        identity_register = json.loads(
            identity_path.read_text(encoding="utf-8-sig")
        )
        for identity in identity_register["identities"]:
            if identity["identity_id"] == "USR-001":
                identity["entity_ids"] = []
        save(identity_path, identity_register)

        blocked = Mock(side_effect=AssertionError("Provider must not run"))
        result = answer(blocked)
        blocked.assert_not_called()
        require(
            result["status"] == "no_evidence"
            and result["citations"] == [],
            "Removed membership still exposed evidence",
        )
        require(
            context()["context"] == "",
            "Removed membership still produced context",
        )
        print("PASS: membership removal excludes context and skips provider")

    print("\nResults: 6 passed; 0 failed")


if __name__ == "__main__":
    main()