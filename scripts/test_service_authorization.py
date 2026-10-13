"""Verify scoped service access and disabling using copied registers."""

import json
import shutil
import tempfile
from pathlib import Path

from authorize_lease import DATA, access_lease


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "data"
        shutil.copytree(DATA, folder)

        result = access_lease("SVC-001", "LEASE-001", folder=folder)
        require(
            result.get("decision") == "allow"
            and result.get("lease", {}).get("entity_id") == "ENT-001",
            "Service should read the North lease",
        )
        print("PASS: service reads its permitted North lease")

        result = access_lease("SVC-001", "LEASE-002", folder=folder)
        require(result == {"decision": "deny"},
                "Service exposed South lease content")
        print("PASS: service is denied South lease content")

        result = access_lease(
            "SVC-001", "LEASE-001", "lease:write", folder=folder
        )
        require(result == {"decision": "deny"},
                "Read-only service received write permission")
        print("PASS: service write attempt is denied")

        path = folder / "identities.json"
        document = json.loads(path.read_text(encoding="utf-8-sig"))
        for identity in document["identities"]:
            if identity["identity_id"] == "SVC-001":
                identity["status"] = "disabled"

        path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8"
        )

        result = access_lease("SVC-001", "LEASE-001", folder=folder)
        require(result == {"decision": "deny"},
                "Disabled service retained access")
        print("PASS: disabling service denies its next access check")

    print("\nResults: 4 passed; 0 failed")


if __name__ == "__main__":
    main()