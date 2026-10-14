# Access Review Procedure

## Scope

Procedure for the synthetic Project 4 identity register.
No actual business-owner certification has been performed.

The generated report remains marked not_reviewed.

## Review responsibilities

- Entity owner: confirms whether entity membership is justified.
- Application owner: confirms required actions and role suitability.
- Service owner: confirms the service purpose and accountable operator.
- Identity administrator: implements approved assignment changes.
- Reviewer: records decisions and verifies remediation evidence.

These are proposed responsibilities, not appointed people.

## 1. Generate the current report

From the repository root:

    python scripts/access_review.py

Record the repository commit and review date.
Preserve the report used for the review.

The report shows configuration at generation time, not historical usage.

## 2. Review every identity

Confirm:

- The identity still has a valid business purpose.
- Its active or disabled status is appropriate.
- Its role permits only necessary actions.
- Each entity membership is justified.
- Service identities have an accountable owner.
- Disabled identities have no effective action scope.

The current register does not contain employment status, service-owner
details or last-use evidence. Obtain those separately in a real review.

## 3. Investigate review flags

| Flag | Review question |
|---|---|
| multi_entity_membership | Does the business need access to each assigned entity? |
| combined_request_and_approval_permissions | Can permissions be separated, and is self-approval still denied? |
| service_assigned_human_only_permissions | Why does the service have permissions the workflow will not honor? |

Flags require investigation. They do not automatically establish misuse.

An identity without flags still requires review.

## 4. Record a decision

For each identity and assignment, record:

- Review identifier and date.
- Identity identifier.
- Entity and action or role under review.
- Decision: retain, remove, modify or investigate.
- Business justification.
- Accountable reviewer.
- Remediation owner and target date where needed.
- Completion evidence.

Do not invent reviewer approval or mark unresolved decisions complete.

## 5. Implement approved changes

Change the identity or role register through a reviewed Git change.

Disabling an identity denies its next application authorization check.
It does not revoke real credentials or terminate external sessions.

Changing a shared role affects every identity assigned to that role.
Assess that impact before editing role permissions.

## 6. Verify remediation

Run:

    python scripts/test_authorize_lease.py
    python scripts/test_authorization_config.py
    python scripts/test_service_authorization.py
    python scripts/test_lease_change_workflow.py
    python scripts/test_approval_boundaries.py
    python scripts/test_access_review.py

Regenerate the report and inspect the affected assignment.

The tests encode the demonstration baseline. An intentional policy
change may require reviewed updates to fixtures and expected results.
Do not weaken denial checks merely to obtain a passing result.

## Completion criteria

A review is complete only when decisions have accountable reviewers
and required remediation is verified or explicitly tracked as unresolved.

Keep certification records separate from the generated report.
Its review_status field is not a certification workflow.

## Limitations

Authentication, credential rotation, session revocation and tamper-resistant
audit storage are outside this demonstration.

Separate file reads do not form an atomic configuration snapshot.
Perform this review while configuration files are not being edited.