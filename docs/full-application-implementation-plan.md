# Full Application Implementation Plan

This implementation plan details the step-by-step development strategy to build the complete researcher-facing application layer over the existing central database.

---

## 1. Phased Development Roadmap

### Phase 1: Global Navigation, Dashboard & Baseline Auditing
* **Goal**: Build a unified global navigation structure, a comprehensive research dashboard displaying system scope and quality, and audit baseline counts.
* **Scope**:
  - Global navigation sidebar and top navbar matching the 17 top-level sections (Dashboard, Search, Entities, Campaign Finance, Government, Projects, Lobbying, Contracts, Sources, Documents, Assertions, Research, Review Queue, Data Quality, Imports, Exports, Administration).
  - Redesign `templates/research/dashboard.html` to display full database counts, review status, research activity, and data-quality indicators.
  - Implement cards that link to filtered views of entities, transactions, and tasks.

### Phase 2: Unified Search, Entity Directory & Profile Page
* **Goal**: Build the full-database unified search view, browsable directories, and expand the Entity Profile into the central hub of the application.
* **Scope**:
  - Search backend querying entities, aliases, FPPC IDs, campaign names, contract scopes, and meeting agenda items.
  - Filter options (entity type, jurisdiction, date range, review status, confidence score, predicate).
  - Browsable directory tabs in `templates/entities/entity_list.html`.
  - Expand `entity_detail.html` to integrate tabs for overview, timeline, relationships, campaigns, committees, and audit logs.

### Phase 3: Assertion Workbench, Ledgers & Modules UI
* **Goal**: Deliver the interactive assertion workbench, financial transaction ledgers, and module views for government, projects, lobbying, and contracts.
* **Scope**:
  - Assertion workbench to create, edit, verify, or dispute assertions with visual page-coordinate locators.
  - Add transaction ledger tables for Contributions, Expenditures, and Loans withCycle and Recipient filtering.
  - Create detail pages for Meetings, Government Bodies, Public Offices, Projects, Lobbying Firms, and Agency Contracts.

### Phase 4: Research Collections & Review Queue
* **Goal**: Deliver the project organization workspace, collection-pinning features, and a unified review queue.
* **Scope**:
  - `ResearchCollection` models and dashboard view, showcasing Muelrath Public Affairs as a seed collection.
  - Task manager, open question registry, and PRA tracking forms.
  - Refactored Review Queue with filters for OCR errors, matching, assertions, and vote extractions.

### Phase 5: Timeline Service & Network Explorer
* **Goal**: Build timeline views, a browser-based Network Explorer, and entity comparison utilities.
* **Scope**:
  - Timelines compiling project actions, campaigns, votes, and contract executions.
  - Interactive network view (e.g. using cytoscape.js or d3.js) plotting entities and assertions.
  - Side-by-side comparison screen checking direct and indirect paths between two entities.

### Phase 6: Data-Quality Center & Import/Export Hub
* **Goal**: Implement system checks, bulk actions, and data ingestion management views.
* **Scope**:
  - Data-Quality Center list highlighting stale provisional status or assertions lacking sources.
  - Import Hub reporting process metrics (rows, errors, version) for workbook and Form 460 ingestion.
  - Export Hub supporting download of visible lists and Gephi-compatible CSVs.

### Phase 7: API, Access Controls & Verification
* **Goal**: Expose REST endpoints, review permissions, run accessibility testing, and build integration tests.
* **Scope**:
  - Authenticated REST API for all major models.
  - Enforce permissions for Administrators, Managers, Researchers, and Reviewers.
  - End-to-end browser test suites.

---

## 2. Verification & Safety Plan

* **Backup Safeguard**: Create sqlite3 copy prior to implementing database changes.
* **Additive Migration Mode**: Migrations must only be additive. No deletion of raw tables.
* **Verification Checks**: Run `pytest` and `python manage.py check` before and after each phase to guarantee zero regression.
