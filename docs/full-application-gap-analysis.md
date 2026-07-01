# Full Application Gap Analysis

This document provides a thorough gap analysis of the current Sonoma County Political Relationship & Influence Database application state versus the requirements for a complete, integrated research environment.

---

## 1. Model-to-UI Coverage Gaps

The database contains a rich set of domain-specific models representing political, civic, financial, and governmental relationships. However, a significant portion of these models lack dedicated web interfaces or CRUD capabilities.

| Django App | Model | Existing UI Coverage | Gap Description |
| :--- | :--- | :--- | :--- |
| **entities** | `Entity` | List and detail views exist. | No creation or inline modification UI. |
| | `Person` | Metadata displayed on entity profile. | No dedicated edit or role assignment UI. |
| | `Organization` | Metadata displayed on entity profile. | No dedicated edit or categorization UI. |
| | `Alias` | Read-only aliases on entity profile. | No interface to add, edit, or archive aliases. |
| | `EntityMerge` | Reversal view exists, but no merge queue UI. | No UI to propose, verify, or review merges. |
| | `Project` | None. | Completely lacks list, detail, and project tracking views. |
| | `GovernmentBody` | None. | No registry or directory UI. |
| | `PublicOffice` | None. | No list or assignment UI. |
| **government** | `Meeting` | None. | No meeting, calendar, or archive workspace. |
| | `AgendaItem` | None. | No agenda detail page or staff recommendation view. |
| | `Motion` | None. | No motion registry, mover/seconder tracking UI. |
| | `Vote` | None. | No vote grid, member voting history, or recusal views. |
| | `Appointment` | None. | No board roster or appointment timeline view. |
| | `Event` | None. | No public event list or calendar UI. |
| **transactions** | `Contribution` | Read-only list exists. | Lack of advanced pagination, filters, and edit views. |
| | `Expenditure` | None. | No ledger, purpose code filtering, or detail view. |
| | `Contract` | None. | No procurement register or award timeline UI. |
| | `LobbyingActivity` | None. | No lobbyist-client register or firm directory UI. |
| | `AuditEvent` | Dashboard has top 10 logs. | Lacks full search, filtering, and detail audit log views. |
| **research** | `ResearchCollection` | None. | Completely lacks collection workspaces or dashboard links. |
| | `ResearchTask` | None. | No task manager or assignment interface. |
| | `OpenQuestion` | None. | No QA panel or investigator workflow. |
| | `PRARequest` | None. | No tracker for public records request logs. |
| | `DataQualityIssue` | None. | No quality dashboard or diagnostic workflow. |

---

## 2. Search & Retrieval Deficiencies

* **Current Implementation**: A single query bar filters the `Entity` canonical name and type in `entity_list` view.
* **Gaps**:
  * No search across OCR text (`DocumentPage.ocr_text` or `extracted_text`).
  * No search across document filenames, alias texts, campaign outcomes, or project descriptions.
  * No search in assertion explanatory notes, lobbyist matters, or motion texts.
  * No persistent filters (jurisdiction, cycle, amount range, confidence level, review status).
  * No saved search support.

---

## 3. Data-Quality & Audit Workspace Gaps

* **Current Implementation**: An `AuditEvent` table is populated during extraction reviews and merges, and the top 10 rows are displayed in the research dashboard.
* **Gaps**:
  * No dedicated **Data Quality Center** to query system warnings (e.g. assertions without sources, duplicate committee IDs, merged entities still receiving imports, invalid dates).
  * No bulk action interface for assigning jurisdictions or staging records to a collection.
  * No UI showing the complete provenance path for assertions (must be checked manually in database).

---

## 4. Technical Debt & Performance Risks

* **N+1 Queries**:
  * Listing views (like `entity_list` and the updated `entity_detail` timeline) query related tables without optimizing database fetches via `select_related` or `prefetch_related`.
* **Database Indexes**:
  * Missing database indexes on foreign keys and search columns, specifically `Entity.status`, `Entity.jurisdiction`, `Assertion.predicate`, `Contribution.review_status`, and `LobbyingActivity.lobbyist_entity`.
* **Soft Deletions**:
  * Deleting a record from the database currently cascades, risking historical audit losses. A soft-delete or archival flag mechanism must be enforced.
