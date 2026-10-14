"""Verify document permission checks and filtering before ranking."""

import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import retrieve_documents as retrieval
from authorize_lease import DATA


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        identities = base / "identities"
        documents = base / "documents"
        shutil.copytree(DATA, identities)
        shutil.copytree(retrieval.DOCUMENT_DATA, documents)

        def search(identity_id, query="maintenance acknowledgement"):
            return retrieval.retrieve(
                identity_id,
                query,
                identity_folder=identities,
                document_folder=documents,
            )

        for identity_id, expected_id in [
            ("USR-001", "DOC-N-001"),
            ("USR-002", "DOC-S-001"),
        ]:
            result = search(identity_id)
            require(
                result["decision"] == "allow"
                and [m["document_id"] for m in result["matches"]]
                == [expected_id],
                f"Incorrect entity results for {identity_id}",
            )
            print(f"PASS: {identity_id} retrieves only its entity document")

        result = search("USR-003")
        require(
            {m["document_id"] for m in result["matches"]}
            == {"DOC-N-001", "DOC-S-001"},
            "Group reader should retrieve both documents",
        )
        print("PASS: explicit group membership permits both documents")

        for identity_id in ["USR-004", "USR-005", "USR-999"]:
            with patch.object(
                retrieval,
                "rank_documents",
                side_effect=AssertionError("Ranking must not run"),
            ):
                result = search(identity_id)
            require(
                result == {"decision": "deny", "matches": []},
                "Denied identity received document information",
            )
            print(f"PASS: {identity_id} denied before ranking")

        original_rank = retrieval.rank_documents
        with patch.object(
            retrieval, "rank_documents", wraps=original_rank
        ) as rank:
            search("USR-001")

        candidates = rank.call_args.args[1]
        require(
            [d["document_id"] for d in candidates] == ["DOC-N-001"],
            "Unauthorized document entered ranking",
        )
        print("PASS: unauthorized document excluded from ranking inputs")

        result = search("USR-001", "astronomy")
        require(
            result == {
                "decision": "allow",
                "retrieval_status": "no_evidence",
                "matches": [],
            },
            "Unmatched query should return no evidence",
        )
        print("PASS: unmatched authorized query returns no evidence")

        path = documents / "documents.json"
        document = json.loads(path.read_text(encoding="utf-8-sig"))
        for record in document["documents"]:
            if record["document_id"] == "DOC-N-001":
                record["status"] = "deleted"
        path.write_text(json.dumps(document), encoding="utf-8")

        result = search("USR-001")
        require(
            result["retrieval_status"] == "no_evidence"
            and result["matches"] == [],
            "Deleted document remained retrievable",
        )
        print("PASS: deleted document is excluded")

    print("\nResults: 9 passed; 0 failed")


if __name__ == "__main__":
    main()