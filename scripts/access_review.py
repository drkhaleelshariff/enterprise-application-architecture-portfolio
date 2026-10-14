"""Report synthetic identity assignments and effective action scope."""

import json
import sys

from authorize_lease import DATA, load_data


def build_review(folder=DATA):
    identities, roles, leases = load_data(folder)
    rows = []

    for identity_id in sorted(identities):
        identity = identities[identity_id]
        assigned = sorted(
            roles[identity["role"]]["allowed_actions"]
        )
        effective = []

        if identity["status"] == "active":
            for action in assigned:
                # Change requests and approvals require human identities.
                if (
                    action != "lease:read"
                    and identity["identity_type"] != "human"
                ):
                    continue

                for entity_id in sorted(identity["entity_ids"]):
                    effective.append({
                        "entity_id": entity_id,
                        "action": action,
                    })

        readable = []
        for lease_id, lease in sorted(leases.items()):
            if {
                "entity_id": lease["entity_id"],
                "action": "lease:read",
            } in effective:
                readable.append(lease_id)

        flags = []
        if len(identity["entity_ids"]) > 1:
            flags.append("multi_entity_membership")

        if {
            "lease_change:request", "lease_change:approve"
        }.issubset(assigned):
            flags.append("combined_request_and_approval_permissions")

        if (
            identity["identity_type"] == "service"
            and any(action != "lease:read" for action in assigned)
        ):
            flags.append("service_assigned_human_only_permissions")

        rows.append({
            "identity_id": identity_id,
            "display_name": identity["display_name"],
            "identity_type": identity["identity_type"],
            "status": identity["status"],
            "role": identity["role"],
            "assigned_entities": sorted(identity["entity_ids"]),
            "assigned_actions": assigned,
            "effective_action_scope": effective,
            "readable_lease_ids": readable,
            "review_flags": flags,
        })

    return {
        "identity_count": len(rows),
        "review_status": "not_reviewed",
        "identities": rows,
        "limitations": [
            "Synthetic authorization configuration; authentication is simulated.",
            "Approval scope does not override request state or self-approval checks.",
            "Flags identify review questions, not automatic policy violations.",
            "No business owner has certified these assignments.",
        ],
    }


def main():
    try:
        report = build_review()
    except (OSError, ValueError, RecursionError):
        print("FAIL: access review configuration is unavailable or invalid",
              file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())