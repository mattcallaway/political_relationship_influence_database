# Data Integrity Baseline

This document establishes the baseline values for data-quality checks across the database.

---

## 1. Quality Indicators

* **Orphan Assertions**: Target baseline is `0`. All assertions must refer to an authoritative source publication.
* **Orphan Transactions**: Target baseline is `0`. Every imported transaction must map back to a PDF source document page coordinate.
* **Verified Records without Reviewer**: Target baseline is `0`. High-priority records changed to `VERIFIED` status must specify the reviewer in `updated_by`.
* **Provisional Records Age Limit**: Default threshold is `30 days`. Provisional machine-extracted actors older than 30 days are flagged for cleanup.

---

## 2. Integrity Checks Baseline Metrics

| Metric | Target | Current Status | Action Status |
| :--- | :--- | :--- | :--- |
| Unlinked Assertions | 0 | 0 | PASSED |
| Unlinked Transactions | 0 | 170 | WAITING (Awaiting Schedule E integration) |
| Duplicate Committee FPPC IDs | 0 | 0 | PASSED |
| Unreviewed Matches | 0 | 0 | PASSED |
