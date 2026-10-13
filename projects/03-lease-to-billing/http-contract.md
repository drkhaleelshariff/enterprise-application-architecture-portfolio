# Accounting HTTP Contract: Version 1

## Status and scope

Proposed contract for the local synthetic accounting demonstration.

The server will listen on 127.0.0.1:8001.
Authentication, TLS and production deployment are outside this version.

## Health endpoint

GET /health

Response: HTTP 200

```json
{
  "status": "ok"
}
```

This indicates that the server is responding. It does not verify
database readiness or end-to-end processing.

## Submit an invoice

POST /v1/postings

Required request Content-Type: application/json.
Maximum request body: 16384 bytes.
Content-Length is required; chunked requests are unsupported.

The request uses the existing invoice schema:

```json
{
  "schema_version": "1",
  "invoice_id": "INV-ENT-001-LEASE-001-2026-11",
  "instruction_id": "BILL-ENT-001-LEASE-001-2026-11",
  "entity_id": "ENT-001",
  "lease_id": "LEASE-001",
  "billing_period": "2026-11",
  "currency": "EUR",
  "amount": "2500.00",
  "accounting_status": "pending"
}
```

Identifiers must match the entity, lease and billing period.
Amounts are nonnegative decimal strings with exactly two decimal places.

The receiver ignores accounting_status when comparing immutable content.
A caller-supplied status cannot establish acceptance.

## Successful responses

First accepted delivery: HTTP 201.

```json
{
  "result": "created",
  "posting_id": "POST-INV-ENT-001-LEASE-001-2026-11",
  "invoice_id": "INV-ENT-001-LEASE-001-2026-11",
  "status": "accepted"
}
```

Identical repeat delivery: HTTP 200, with result set to existing.

Return acceptance only after the accounting transaction commits.

## Error responses

All application responses use Content-Type: application/json.

| HTTP status | Meaning |
|---|---|
| 400 | Invalid JSON, duplicate JSON keys or malformed request length |
| 404 | Unknown path |
| 405 | Unsupported method for a known path |
| 409 | Existing invoice ID has different immutable content |
| 411 | Required Content-Length is missing |
| 413 | Request body exceeds the size limit |
| 415 | Unsupported request media type |
| 422 | Invoice fields or values fail validation |
| 503 | Accounting storage is unavailable |
| 500 | Unexpected server error |

Example:

```json
{
  "error": "invoice_conflict",
  "message": "Invoice ID already posted with different content"
}
```

Server errors must not return internal database paths or tracebacks.

## Client behavior

- Use a finite request timeout.
- Verify the acknowledgement identifies the submitted invoice.
- Mark billing acknowledged only after a valid acceptance response.
- Treat timeout or connection failure as an uncertain outcome.
- Retry the same immutable invoice using the same invoice ID.
- Do not automatically retry validation errors or content conflicts.
- Keep retries bounded and record unresolved failures.

## Verification plan

Test first delivery, repeat delivery, conflicting content, invalid
requests, server unavailability and lost-confirmation recovery.

Verify that repeated submissions retain one accounting posting.

## Limitations

This contract does not provide authentication or entity authorization.
Entity identifiers provide traceability, not access enforcement.

There is no atomic transaction across billing and accounting.
Reconciliation remains necessary.