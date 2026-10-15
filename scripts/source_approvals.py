"""Load application-controlled approvals for exact source versions."""

import json
import re
from pathlib import Path

from authorize_lease import unique_object


def load_approvals(path):
    """Return approved (document_id, version) pairs or raise an error."""
    with Path(path).open(encoding="utf-8-sig") as handle:
        register = json.load(handle, object_pairs_hook=unique_object)

    if (
        not isinstance(register, dict)
        or set(register) != {"schema_version", "approved_sources"}
        or register["schema_version"] != "1"
        or not isinstance(register["approved_sources"], list)
    ):
        raise ValueError("Invalid source approval register")

    approved = set()

    for row in register["approved_sources"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"document_id", "version"}
        ):
            raise ValueError("Invalid source approval fields")

        document_id = row["document_id"]
        version = row["version"]

        if (
            not isinstance(document_id, str)
            or not document_id.strip()
            or document_id != document_id.strip()
            or not isinstance(version, str)
            or re.fullmatch(r"[1-9][0-9]*", version) is None
        ):
            raise ValueError("Invalid source approval value")

        key = (document_id, version)
        if key in approved:
            raise ValueError("Duplicate source approval")

        approved.add(key)

    return approved