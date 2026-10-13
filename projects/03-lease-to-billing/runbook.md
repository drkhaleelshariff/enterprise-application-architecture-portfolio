# Lease-to-Billing Demonstration Runbook

## Scope

Local Windows demonstration using Python and synthetic data.
No third-party packages are required.

Run commands from the repository root.
Use separate Command Prompt windows for the server and client.

## 1. Run isolated verification

These tests create temporary databases and do not require the working
accounting server:

```bat
python scripts\test_lease_to_billing.py
python scripts\test_store_invoice.py
python scripts\test_accounting_receiver.py
python scripts\test_submit_to_accounting.py
python scripts\test_reconcile_invoices.py
python scripts\test_accounting_http.py
python scripts\test_http_handoff.py
python scripts\test_http_lost_confirmation.py
python scripts\test_http_contract_edges.py
```

Expected passing check counts, respectively:
2, 5, 5, 6, 6, 11, 5, 4 and 5.

Check each command's exit code immediately:

```bat
echo %ERRORLEVEL%
```

Expected: 0. Stop and investigate any traceback or nonzero result.

## 2. Store the example invoice

In the client window:

```bat
python scripts\store_invoice.py
```

First delivery returns created. An identical repeat returns existing.
Conflicting content under the same instruction ID is rejected.

This creates the runtime folder and billing database if needed.

## 3. Start accounting

In the server window:

```bat
python scripts\accounting_http_server.py
```

Leave this window running. Only one working server should use port 8001.

In the client window:

```bat
curl.exe -i --max-time 5 http://127.0.0.1:8001/health
```

Expected: HTTP 200 and {"status": "ok"}.
Health confirms server responsiveness, not database readiness.

## 4. Submit the stored invoice

```bat
python scripts\submit_to_accounting_http.py
echo %ERRORLEVEL%
```

Expected: accounting_status acknowledged and exit code 0.

Accounting result is created on first acceptance or existing on repeat.
Billing records acknowledgement only after validating the response.

## 5. Reconcile

While no other process is writing:

```bat
python scripts\reconcile_invoices.py
echo %ERRORLEVEL%
```

For the single example invoice, expect one fully matched record and
zero issues.

Exit codes:
- 0: comparison completed without issues.
- 1: inconsistencies detected.
- 2: comparison could not complete.

The two databases are read separately, without a synchronized snapshot.

## Failure handling

| Symptom | Action |
|---|---|
| Connection refused | Check that the server is running on port 8001; retry the same invoice after recovery |
| Timeout or connection closes | Treat outcome as uncertain; reconcile and retry the unchanged invoice |
| HTTP 409 conflict | Investigate the existing and submitted content; do not overwrite or assign a new ID merely to bypass the conflict |
| HTTP 422 validation error | Correct the invalid input through the appropriate workflow before resubmission |
| HTTP 503 storage unavailable | Investigate accounting storage; retain the invoice and retry after recovery |
| Missing accounting posting | Investigate the handoff and submit the unchanged stored invoice when appropriate |
| Confirmation not recorded | Verify matching accounting content; retry the unchanged stored invoice |
| Content or posting-ID mismatch | Stop recovery for that record and investigate |
| Unexpected accounting posting | Investigate its origin and missing billing record |

Retries are manual in this baseline. There is no automatic retry scheduler
or persisted attempt history.

## Lost confirmation

Accounting may commit before its response is lost.
Billing then remains pending even though a posting exists.

Retrying the same immutable invoice returns the existing posting.
The client can then record acknowledgement without creating a duplicate.

Do not assume a failed response means accounting performed no work.

## Storage

Working databases are under:

- projects/03-lease-to-billing/runtime/billing.sqlite3
- projects/03-lease-to-billing/runtime/accounting.sqlite3

The runtime folder is excluded from Git.
Do not delete databases as a routine recovery action.

## Stop

Press Ctrl+C in the server window.
Database records remain saved for the next session.

## Limits

This baseline uses local HTTP without authentication or TLS.
It is not a production server or a real accounting implementation.

No atomic transaction spans billing and accounting.
Recovery depends on repeat-safe posting and reconciliation.

Some HTTP contract cases remain untested, including missing
Content-Length. The client timeout is a socket-operation timeout,
not a guaranteed total execution deadline.