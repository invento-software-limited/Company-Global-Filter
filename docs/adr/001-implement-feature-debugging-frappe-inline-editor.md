# ADR 001: Implement Feature: Debugging Frappe Inline Editor

Date: 2026-08-04
Status: Accepted

## Context
During inline editing backend validation, we discovered that permission-checking was bypassed on the server-side, and multiple field updates (bulk update) could cause database transaction state leakage if one document update failed, leading to aborted transaction errors (especially under PostgreSQL).

## Decision
1. Implement settings-based validation on both single-field updates and bulk updates, ensuring the target field is defined as editable within the active `Inline Editor Settings` document.
2. Utilize database savepoints (`frappe.db.savepoint()`) inside loops in `bulk_update` and `run_bulk_update_job` to isolate changes of each document and roll back individual failures cleanly without polluting or corrupting the global transaction.

## Consequences
- **Benefits**:
  - Secure APIs that cannot be bypassed via custom REST calls.
  - Transactions are handled robustly; if one document update fails, other document updates in the same request are still applied and saved.
- **Trade-offs / Risks**:
  - Requires additional queries to check `Inline Editor Settings` on each field update (mitigated by Frappe's document caching).
