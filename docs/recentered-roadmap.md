# Recentered Platform Roadmap

This roadmap redirects database development toward researcher-facing workflows, evidence integrity, and connection analysis, replacing the previous parser-driven pipeline stages.

---

## Phase 1: Mission and Integrity (Status: COMPLETED)
Establish data models and strict guidelines to guarantee provenance and prevent product drift.
* **Project Charter**: Formalize evidence-backed tenets and non-judgmental directives.
* **Product Soul Audit**: Review campaign-finance centricity and OCR dependencies.
* **Anti-Drift Principles**: Enforce the 10 development rules.
* **Research Question Matrix**: Map core questions to required schemas, identifying gaps.
* **Database Inventory & Counts**: Validate baseline ingestion metrics.

---

## Phase 2: Complete Researcher Workspace (Status: IN PROGRESS)
Build interfaces where researchers can collect evidence, navigate documents, and collaborate on inquiries.
* **Muelrath Investigation Workspace (Next Milestone)**: Overhaul `ResearchCollection` templates to serve as an active investigative dashboard.
* **Complete Entity Profiles**: Consolidate cross-domain tables (contributions, expenditures, lobbying, appointments, votes, board term limits) into the main profile view.
* **Document and Source Workspace**: Build a page-by-page PDF browser overlay showing extracted fields, enabling OCR correction, and linking locators to assertions.
* **Unified Review Queue**: Integrate one-click approval workflows for contributions, assertions, and provisional matches.
* **Research Tasks & Open Questions**: Implement trackers for inquiries, source gaps, and public records (PRA) requests.

---

## Phase 3: Financial and Professional Relationships (Status: PLANNED)
Expand campaign finance models beyond Schedule A to cover expenditure trails and consultants.
* **Schedule E Expenditures**: Ingest and reconcile committee spending records.
* **Campaign Vendor & Consultant Maps**: Link campaign committees to firms, subcontractors, and treasurers.
* **Filing Amendments**: Implement reconciliation logic where amended Form 460 filings mark prior rows as superseded.

---

## Phase 4: Government and Project Relationships (Status: PLANNED)
Connect private actors to government boards, planning approvals, and lobbying contracts.
* **Board Appointments**: Track concurrent term limits, appointers, and seats.
* **Public Contracts**: Log vendor awards, agency sign-offs, and project budgets.
* **Roll-Call Votes**: Map agenda items, motions, movers/seconders, and individual votes.
* **Lobbying Registry Linkage**: Associate lobbying disclosures with targets and compensation.

---

## Phase 5: Connection Analysis & Projections (Status: PLANNED)
Visualize and query connection networks without imposing automatic assumptions of influence.
* **Evidence-Backed Network**: Graph projection where every edge displays origin record types, confidence scores, and source locators.
* **Visual Filtering**: Enable filtering by relationship type, date ranges, jurisdictions, and collections.
* **Chronological Timeline overlapping**: Correlate meetings, campaign contributions, and contracts chronologically.
* **Entity Comparison**: Display side-by-side timelines and transaction overlapping between two profiles.

---

## Phase 6: Operations & Methodology (Status: PLANNED)
Ensure system stability, publication reviews, and public methodology disclosures.
* **Quality Controls & Diagnostics**: Automate duplication alerts and empty relation notifications.
* **Database Operations**: Maintain automated backups and transactional batch rollbacks.
* **Public/Private Separation**: Guard unpublished research collections and internal notes.
* **Methodology Display**: Publish system documentation clarifying connection interpretations.
