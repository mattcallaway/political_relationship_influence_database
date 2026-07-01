# Remaining Platform Roadmap: Sonoma Civic Research Platform

This document outlines the structured development path for scaling the Sonoma County Political Relationship & Influence Database into a comprehensive, robust research platform.

---

## Phase A: Database Verification and Research Reliability

### A1: Database Inventory Command
* **Problem Addressed**: Lack of an automated, read-only mechanism to verify database status.
* **User Value**: Provides researchers with immediate, auditable evidence counts.
* **Dependencies**: None.
* **Estimated Complexity**: Small.
* **Data Migration**: No.
* **Risk Level**: Very Low.
* **Acceptance Criteria**: Running `python manage.py database_inventory_report` compiles correct table counts and prints JSON or Markdown.
* **Recommended Phase**: Phase A (Milestone 1).
* **Tests Required**: Command stdout asserts, format validations.

### A2: Source-Provenance Verification
* **Problem Addressed**: Orphans without source links degrade dataset credibility.
* **User Value**: Guarantees every claim/entity links back to public records.
* **Dependencies**: A1.
* **Estimated Complexity**: Medium.
* **Data Migration**: No.
* **Risk Level**: Low.
* **Acceptance Criteria**: Script detects assertions/transactions without `SourceLocator` or `Source` references.
* **Recommended Phase**: Phase A (Milestone 1).
* **Tests Required**: Unlinked record detection checks.

---

## Phase B: Complete Financial and Campaign-Vendor Model

### B1: Expenditure Ingestion & Campaign Vendor Profiles
* **Problem Addressed**: The database focuses on contributions but lacks campaign spending tracking.
* **User Value**: Exposes which political consulting and PR firms are receiving funds.
* **Dependencies**: Phase A.
* **Estimated Complexity**: Large.
* **Data Migration**: Yes (add Expenditure schema attributes).
* **Risk Level**: Medium.
* **Acceptance Criteria**: Ingest Schedule E expenditure CSV/Excel sheets, create Campaign Vendor categories, list payees.
* **Recommended Phase**: Phase B (Milestone 1).
* **Tests Required**: Expenditure ledger view tests, CSV import checks.

### B2: Subcontractor and Intermediary Tracking
* **Problem Addressed**: Prime political consultants hide sub-consultant spending.
* **User Value**: Exposes subcontractor relationships.
* **Dependencies**: B1.
* **Estimated Complexity**: Medium.
* **Data Migration**: No.
* **Risk Level**: Low.
* **Acceptance Criteria**: Expenditures link to a sub-vendor when disclosed.
* **Recommended Phase**: Phase B.
* **Tests Required**: Intermediary relation checks.

---

## Phase C: Full-Picture Entity Investigation

### C1: Enhanced Entity Overview & Multi-Tab Hub
* **Problem Addressed**: Researchers must navigate multiple pages to understand an entity's connections.
* **User Value**: Aggregates timeline events, contracts, appointments, lobbying, and campaign finance into a single screen.
* **Dependencies**: Phase A & B.
* **Estimated Complexity**: Medium.
* **Data Migration**: No.
* **Risk Level**: Low.
* **Acceptance Criteria**: Profiles display complete relational cards linked to source provenance.
* **Recommended Phase**: Phase C (Milestone 1).
* **Tests Required**: View response checks, context data validations.

---

## Phase D: Interactive Network Explorer

### D1: Cytoscape/D3 Graph Visualizer
* **Problem Addressed**: Relational tables cannot show complex indirect networks.
* **User Value**: Renders interactive nodes (entities) and edges (assertions, contributions, contracts, votes).
* **Dependencies**: Phase C.
* **Estimated Complexity**: Large.
* **Data Migration**: No.
* **Risk Level**: Medium.
* **Acceptance Criteria**: Renders Cytoscape graphs with filters for confidence, verification status, and date.
* **Recommended Phase**: Phase D.
* **Tests Required**: JSON element compiler checks.

---

## Phase E: Entity Comparison

### E1: Overlap & Path Analyzer
* **Problem Addressed**: Identifying shared campaign consultants, donors, or government contract overlaps manually is time-consuming.
* **User Value**: Side-by-side comparison screen exposing direct and indirect paths (degree 2).
* **Dependencies**: Phase D.
* **Estimated Complexity**: Medium.
* **Data Migration**: No.
* **Risk Level**: Low.
* **Acceptance Criteria**: Compares two entities and lists direct relationships and shared neighbor intersections.
* **Recommended Phase**: Phase E.
* **Tests Required**: Pathfinding algorithm verification checks.

---

## Phase F: Research Collection Command Center

### F1: Portfolios & Progress Tracking
* **Problem Addressed**: Collaborative projects lack unified workspace summaries.
* **User Value**: Dashboard grouping collections (e.g. Muelrath Public Affairs) with timelines, task checklists, and PRA request trackers.
* **Dependencies**: Phase C.
* **Estimated Complexity**: Medium.
* **Data Migration**: No.
* **Risk Level**: Low.
* **Acceptance Criteria**: Workspace lists represented entity types, financial totals, and outstanding questions.
* **Recommended Phase**: Phase F (Milestone 1).
* **Tests Required**: Collection summary rendering asserts.

---

## Phase G: Review, Publication, and Governance

### G1: Role-Based Moderation Workflows
* **Problem Addressed**: Machine-extracted data could publish unreviewed errors.
* **User Value**: Clear distinction between provisional, reviewed, and verified records.
* **Dependencies**: Phase F.
* **Estimated Complexity**: Large.
* **Data Migration**: Yes (Reviewer logs on models).
* **Risk Level**: High (breaks access paths if not isolated).
* **Acceptance Criteria**: Restricted, Internal, and Public states with audit history logging reviewer assignments.
* **Recommended Phase**: Phase G.
* **Tests Required**: Permission level asserts, transition state validation tests.

---

## Phase H: Operations and Long-Term Reliability

### H1: Database Health & Backup Routines
* **Problem Addressed**: Database degradation or data loss risks.
* **User Value**: Automated, tested restore protocols and failed ingestion queues.
* **Dependencies**: None.
* **Estimated Complexity**: Medium.
* **Data Migration**: No.
* **Risk Level**: Low.
* **Acceptance Criteria**: Auto backups execute daily; imports can be rolled back safely.
* **Recommended Phase**: Phase H.
* **Tests Required**: Ingest rollback tests.
