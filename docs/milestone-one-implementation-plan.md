# Milestone One Implementation Plan: Complete Researcher-Facing Workspace

This document defines the technical design and execution strategy for **Milestone One**, bridging the gap between independent database modules and a unified civic research platform.

---

## 1. Database Inventory & Verification (Part 1)

### Technical Approach
* **Management Command**: Implement `python manage.py database_inventory_report` in `apps/research/management/commands/database_inventory_report.py`.
  - Supports `--json`, `--markdown`, `--output`, `--collection`, `--jurisdiction`, and `--include-quality-checks`.
  - Performs read-only queries calculating exact model counts and data-integrity diagnostic metrics.
* **Dashboard Summary**: Add an inventory summaries card to the top of `/research/` dashboard.
* **Verification Methods**: Write docs explaining how workbook counts compare with current totals.

---

## 2. Enhanced Entity Investigation (Part 2)

### Technical Approach
* **Summary Panel**: Update `templates/entities/entity_detail.html` with a prominent metadata panel showing type, status, jurisdiction, aliases, and counts.
* **Domain Grid Layout**: Group connected items into multi-tab cards or a structured grid:
  - Financial, Campaign, Professional, Governmental, Project, Lobbying, Civic/Board, and Assertions.
  - Every connection includes a link to the originating transaction, contract, vote, or source page locator.

---

## 3. Expenditure & Campaign Vendor Foundation (Part 3)

### Technical Approach
* **Central Model Review**: Inspect the current `Expenditure` model in `apps/transactions/models.py`. Ensure fields for paying committee, payee, transaction date, amount, code, agent/contractor, filing ID, schedule, source locator, review status, and superseded-by links exist.
* **Campaign Vendor Integration**: Define campaign vendors as canonical `Entity` records linked through `Expenditure` transactions. No separate vendor table is created, maintaining relational consistency.
* **Expenditure Ledger & Forms**:
  - **List View**: Create `/transactions/expenditures/` with filters for payee, committee, code, and date.
  - **Detail View**: Create detailed expenditure inspect layout.
  - **Manual Entry Form**: Add a CREATE/EDIT assertion-style view for manual expenditure entry.
  - **Generic CSV Import**: Add an administrative/investigator command or form to import expenditure tables.

---

## 4. Expanded Data-Quality Diagnostics (Part 4)

### Technical Approach
* **Diagnostics Model**: Review/create `DataQualityIssue` in `apps/research/models.py` tracking severity, description, related record identifiers, detection date, resolution state, and audit logs.
* **Dynamic Scanners**: Register checkers checking duplicate transactions, original/amended filers conflicts, unreviewed auto-matches, and mismatched committee entities.

---

## 5. Research Collection Summaries (Part 5)

### Technical Approach
* **Workspace Overview**: Overhaul `templates/research/collection_detail.html` to show portfolio summaries, timeline charts, financial totals (contributions + expenditures), and represented campaign vendors.
* **Muelrath Portfolio Ingestion**: Seed and link Robert Muelrath, campaign committees, expenditures, and lobbying records in the Muelrath portfolio.

---

## 6. Verification Plan

### Automated Tests
* **Unit Tests**: Asserts for record counts, JSON/Markdown outputs, duplicate detection, and manual expenditure creations.
* **Browser Tests**: Execute flow: Open dashboard -> Inspect inventory -> Search Muelrath -> Open profile -> Create manual expenditure -> Resolve data-quality issue.
* **Performance Checks**: Assert query counts remain below 30 for dashboards and profiles.
