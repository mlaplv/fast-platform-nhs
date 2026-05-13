# Walkthrough: Implement Persistent Diagnostic Counter in Database

## 1. Problem
The diagnostic counter is currently derived from a static `.env` variable and only increments locally in the browser session. This means the progress is lost on page reload and not shared across users.

## 2. Solution
- **Backend**: Modify `DiagnosticAgent.analyze` to increment a persistent `diagnostics_count` field within the product's JSONB metadata in the database upon each successful analysis.
- **Frontend**: Update `MobileDiagnostics.svelte` to display the count from `product.metadata.diagnostics_count`. If unavailable, it falls back to the legacy `.env` calculation.

## 3. Evidence
Implemented a persistent, "honest" diagnostic counter:
- **Backend**: Updated `DiagnosticAgent.py` to increment `diagnostics_count` in the product's JSONB metadata upon each successful AI analysis. If the field doesn't exist, it initializes using the `PUBLIC_G_BY_COUNT * 5` formula.
- **Frontend**: Updated `MobileDiagnostics.svelte` to read directly from `metadata.diagnostics_count`.
- **Real-time Feedback**: Kept the `sessionIncrement` logic to provide immediate visual feedback while the user is still on the page, before the next server-side data refresh.
- **Persistence**: The count now persists across different users and sessions because it is stored in the database.

