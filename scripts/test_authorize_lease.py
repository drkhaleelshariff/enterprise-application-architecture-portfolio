"""Verify entity authorization and identity disabling with copied data."""

import json
import shutil
import tempfile
from pathlib import Path

from authorize_lease import DATA, access_lease


def check(folder, identity, lease, action, allowed):
    result = access_lease(identity, lease, action, folder=folder)

    if allowed:
        if (
            result.get("decision") != "allow"
            or result.get("lease", {}).get("lease_id") != lease
        ):
            raise AssertionError(f"Expected allowed access: {result}")
    elif result != {"decision": "deny"}:
        raise AssertionError(f"Expected denial without record content: {result}")


def main():
    cases = [
        ("North reads North", "USR-001", "LEASE-001", "lease:read", True),
        ("North denied South", "USR-001", "LEASE-002", "lease:read", False),
        ("South reads South", "USR-002", "LEASE-002", "lease:read", True),
        ("South denied North", "USR-002", "LEASE-001", "lease:read", False),
        ("Group reads North", "USR-003", "LEASE-001", "lease:read", True),
        ("Group reads South", "USR-003", "LEASE-002", "lease:read", True),
        ("Disabled denied North", "USR-004", "LEASE-001", "lease:read", False),
        ("Disabled denied South", "USR-004", "LEASE-002", "lease:read", False),
        ("Unknown identity denied", "USR-999", "LEASE-001", "lease:read", False),
        ("Unknown record denied", "USR-001", "LEASE-999", "lease:read", False),
        ("Write denied", "USR-001", "LEASE-001", "lease:write", False),
        ("Unknown action denied", "USR-001", "LEASE-001", "unknown", False),
    ]

    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "data"
        shutil.copytree(DATA, folder)

        for name, identity, lease, action, allowed in cases:
            check(folder, identity, lease, action, allowed)
            print(f"PASS: {name}")

        # Disable a previously permitted identity in the copied register.
        path = folder / "identities.json"
        document = json.loads(path.read_text(encoding="utf-8-sig"))

        for identity in document["identities"]:
            if identity["identity_id"] == "USR-001":
                identity["status"] = "disabled"

        path.write_text(
            json.dumps(document, indent=2) + "\n",
            encoding="utf-8",
        )

        check(folder, "USR-001", "LEASE-001", "lease:read", False)
        print("PASS: disabling identity denies its next access check")

    print("\nResults: 13 passed; 0 failed")


if __name__ == "__main__":
    main()