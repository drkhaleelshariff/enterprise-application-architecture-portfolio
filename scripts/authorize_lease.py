"""Demonstrate entity-scoped authorization with synthetic identities."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "projects" / "04-identity-access" / "data"
ENTITIES = {"ENT-001", "ENT-002"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def load_register(folder, filename, collection, fields, id_field):
    with (Path(folder) / filename).open(encoding="utf-8-sig") as handle:
        document = json.load(handle, object_pairs_hook=unique_object)

    if (
        not isinstance(document, dict)
        or set(document) != {"schema_version", collection}
        or document["schema_version"] != "1"
        or not isinstance(document[collection], list)
        or not document[collection]
    ):
        raise ValueError("Invalid register structure")

    records = {}
    for row in document[collection]:
        if not isinstance(row, dict) or set(row) != fields:
            raise ValueError("Invalid record fields")

        for field, value in row.items():
            if field not in {"entity_ids", "allowed_actions"}:
                if (
                    not isinstance(value, str)
                    or not value
                    or value != value.strip()
                ):
                    raise ValueError("Invalid string field")

        identifier = row[id_field]
        if identifier in records:
            raise ValueError("Duplicate record identifier")
        records[identifier] = row

    return records


def load_data(folder):
    identities = load_register(
        folder, "identities.json", "identities",
        {
            "identity_id", "display_name", "identity_type",
            "status", "role", "entity_ids",
        },
        "identity_id",
    )
    roles = load_register(
        folder, "roles.json", "roles",
        {"role_id", "allowed_actions"}, "role_id",
    )
    leases = load_register(
        folder, "leases.json", "leases",
        {
            "lease_id", "entity_id", "property_id", "tenant_name",
            "currency", "monthly_fixed_rent",
        },
        "lease_id",
    )

    for role in roles.values():
        actions = role["allowed_actions"]
        if (
            not isinstance(actions, list)
            or any(
                not isinstance(action, str)
                or action not in {
                    "lease:read",
                    "lease_change:request",
                    "lease_change:approve",
                }
                for action in actions
            )
            or len(actions) != len(set(actions))
        ):
            raise ValueError("Invalid role actions")

    for identity in identities.values():
        memberships = identity["entity_ids"]
        if (
            identity["identity_type"] not in {"human", "service"}
            or identity["status"] not in {"active", "disabled"}
            or identity["role"] not in roles
            or not isinstance(memberships, list)
            or any(
                not isinstance(entity, str) or entity not in ENTITIES
                for entity in memberships
            )
            or len(memberships) != len(set(memberships))
        ):
            raise ValueError("Invalid identity configuration")

    for lease in leases.values():
        if (
            lease["entity_id"] not in ENTITIES
            or lease["currency"] != "EUR"
            or not re.fullmatch(
                r"[0-9]+\.[0-9]{2}", lease["monthly_fixed_rent"]
            )
        ):
            raise ValueError("Invalid lease configuration")

    return identities, roles, leases


def access_lease(identity_id, lease_id, action="lease:read", folder=DATA):
    # Reload each time so disabling an identity affects the next check.
    identities, roles, leases = load_data(folder)

    identity = identities.get(identity_id)
    lease = leases.get(lease_id)
    denied = {"decision": "deny"}

    if identity is None or identity["status"] != "active":
        return denied

    if lease is None or action != "lease:read":
        return denied

    role = roles[identity["role"]]
    if action not in role["allowed_actions"]:
        return denied

    if lease["entity_id"] not in identity["entity_ids"]:
        return denied

    return {"decision": "allow", "lease": dict(lease)}


def main():
    if len(sys.argv) not in {3, 4}:
        print(
            "Usage: python scripts/authorize_lease.py "
            "identity_id lease_id [action]",
            file=sys.stderr,
        )
        return 2

    action = sys.argv[3] if len(sys.argv) == 4 else "lease:read"

    try:
        result = access_lease(sys.argv[1], sys.argv[2], action)
    except (OSError, ValueError, RecursionError):
        print(json.dumps({
            "decision": "deny",
            "error": "configuration_unavailable",
        }, indent=2))
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["decision"] == "allow" else 1


if __name__ == "__main__":
    sys.exit(main())