"""Verify access-review scope against authorization decisions."""

import json
import shutil
import tempfile
from pathlib import Path

from access_review import build_review
from authorize_lease import DATA, access_lease, load_data


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / "data"
        shutil.copytree(DATA, folder)

        report = build_review(folder)
        rows = {
            row["identity_id"]: row
            for row in report["identities"]
        }

        require(
            report["identity_count"] == 7
            and report["review_status"] == "not_reviewed",
            "Incorrect report count or review status",
        )
        print("PASS: seven identities remain explicitly unreviewed")

        disabled = rows["USR-004"]
        require(
            disabled["assigned_actions"] == ["lease:read"]
            and disabled["effective_action_scope"] == []
            and disabled["readable_lease_ids"] == [],
            "Disabled identity has effective access",
        )
        print("PASS: disabled assignments grant no effective access")

        group = rows["USR-003"]
        require(
            group["readable_lease_ids"] == ["LEASE-001", "LEASE-002"]
            and "multi_entity_membership" in group["review_flags"],
            "Group scope or review flag is incorrect",
        )
        print("PASS: multi-entity access is flagged for review")

        _, _, leases = load_data(folder)
        for identity_id, row in rows.items():
            actual = sorted(
                lease_id
                for lease_id in leases
                if access_lease(
                    identity_id, lease_id, folder=folder
                )["decision"] == "allow"
            )
            require(
                actual == row["readable_lease_ids"],
                f"Report disagrees with authorization for {identity_id}",
            )
        print("PASS: reported readable leases match authorization")

        roles_path = folder / "roles.json"
        roles = json.loads(roles_path.read_text(encoding="utf-8-sig"))
        for role in roles["roles"]:
            if role["role_id"] == "lease_change_requester":
                role["allowed_actions"].append("lease_change:approve")
        roles_path.write_text(json.dumps(roles), encoding="utf-8")

        identities_path = folder / "identities.json"
        identities = json.loads(
            identities_path.read_text(encoding="utf-8-sig")
        )
        for identity in identities["identities"]:
            if identity["identity_id"] == "SVC-001":
                identity["role"] = "lease_change_approver"
        identities_path.write_text(json.dumps(identities), encoding="utf-8")

        changed = {
            row["identity_id"]: row
            for row in build_review(folder)["identities"]
        }

        require(
            "combined_request_and_approval_permissions"
            in changed["USR-005"]["review_flags"],
            "Combined permissions were not flagged",
        )
        print("PASS: combined request and approval permissions are flagged")

        service = changed["SVC-001"]
        require(
            "service_assigned_human_only_permissions"
            in service["review_flags"]
            and service["effective_action_scope"] == [{
                "entity_id": "ENT-001",
                "action": "lease:read",
            }],
            "Service human-only permission handling is incorrect",
        )
        print("PASS: service human-only assignment is flagged and excluded")

    print("\nResults: 6 passed; 0 failed")


if __name__ == "__main__":
    main()