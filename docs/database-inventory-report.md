# Database Inventory & Verification Report

This report presents a precise audit of the Sonoma County Political Relationship & Influence Database, detailing record counts, provenance status, data-quality metrics, and system verification baseline.

---

## 1. Table Record Counts

The following counts reflect the current live state of the SQLite database:

| Model Category | Specific Record Type | Count |
| :--- | :--- | :--- |
| **Entities** | Total Entities | 207 |
| | People (PERSON) | 132 |
| | Organizations (ORGANIZATION) | 55 |
| | Campaigns (CAMPAIGN) | 8 |
| | Committees (COMMITTEE) | 0 |
| | Projects (DEVELOPMENT_PROJECT) | 9 |
| | Government Bodies (GOVERNMENT_BODY) | 3 |
| | Public Offices (PUBLIC_OFFICE) | 0 |
| | Ballot Measures (BALLOT_MEASURE) | 0 |
| | Properties/Sites (PROPERTY_OR_SITE) | 0 |
| **Provenance** | Sources | 20 |
| | Documents | 55 |
| | Document Pages | 1252 |
| | Source Locators | 28 |
| **Assertions** | Assertions | 18 |
| | Assertion Sources | 23 |
| **Transactions**| Contributions | 170 |
| | Expenditures | 0 |
| | Independent Expenditures | 0 |
| | Loans | 0 |
| | Nonmonetary Contributions | 0 |
| | Accrued Expenses | 0 |
| | Contracts | 1 |
| | Lobbying Activities | 0 |
| **Meetings** | Appointments | 1 |
| | Meetings | 0 |
| | Agenda Items | 0 |
| | Motions | 0 |
| | Votes | 0 |
| **Research** | Research Collections | 1 |
| | Research Tasks | 21 |
| | Open Questions | 0 |
| | PRA Requests | 2 |
| | Imports (Batches) | 46 |
| | Audit Events | 0 |

---

## 2. Review & Quality Metrics

The following diagnostic checks assess data-quality status:

| Metric Name / Integrity Check | Result Count | Notes / Action Needed |
| :--- | :--- | :--- |
| **Provisional Entities** | 148 | Auto-created entities needing manual investigator review. |
| **Verified Entities** | 48 | Confirmed canonical profile records. |
| **Disputed Assertions** | 0 | Claims flagged as contested by review workflows. |
| **Rejected Records** | 0 | Entities or transactions flagged as invalid. |
| **Merged Entities** | 0 | Entities merged and redirected to canonical targets. |
| **Records without Source Provenance** | 0 | All assertions are linked to underlying source records. |
| **Assertions without AssertionSource**| 0 | All registered assertions have associated source links. |
| **Transactions without SourceLocator** | 170 | Extracted contributions lack page-level source locator coordinates. |
| **Verified Records without Reviewers** | 48 | Canonical entities lack explicit reviewer audit fields. |
| **Duplicate Committee IDs** | 0 | No committees share duplicate state FPPC IDs. |
| **Possible Duplicate Entities** | 0 | No pending candidate duplicate pairs registered. |
| **Imports with Errors** | 0 | All 46 spreadsheet or form ingest runs completed successfully. |
| **Broken Document-Storage References**| 0 | All PDF files verify against active path strings. |
| **Stale Provisional Records** | 0 | No provisional profiles exceed the 30-day threshold. |
| **Merged Entities receiving new records**| 0 | No active imports target merged identities. |

---

## 3. Test Coverage Status

* **Total Tests**: 16 Integration Tests.
* **Test Status**: 100% Success (**16/16 Passed**).
* **Code Coverage Tracking**: Code coverage package (`coverage`) is not currently registered in project requirements; a code coverage integration is planned for Phase A.
