# Researcher Workspace Explainer & Walkthrough

This document serves as a guide for using the **Sonoma County Political Relationship & Influence Database** workspace.

---

## 1. Information Architecture & Navigation

The platform features a sticky left-hand **Global Sidebar Navigation** that groups the 17 operational modules into logical categories:

```
┌────────────────────────────────────────────────────────┐
│                     CORE WORKSPACE                     │
│ ├─ Dashboard (Live database counts & audits)           │
│ ├─ Search (Unified full-database text queries)         │
│ ├─ Entities (Browsable profiles directory)             │
│ ├─ Campaign Finance (Contributions ledger)              │
│ ├─ Government (Boards, meetings & votes)               │
│ ├─ Projects (Development & land-use tracking)          │
│ ├─ Lobbying (Advocacy & firm client relations)         │
│ └─ Contracts (Public procurement awards)               │
├────────────────────────────────────────────────────────┤
│                 EVIDENTIARY FOUNDATIONS                │
│ ├─ Sources (Authoritative publications)                │
│ ├─ Documents (Ingested files and processing status)    │
│ └─ Assertions (Directed graph relationship edges)       │
├────────────────────────────────────────────────────────┤
│                 INVESTIGATOR WORKBENCH                 │
│ ├─ Research (Portfolios & Collections)                 │
│ ├─ Review Queue (Pending transaction & profile links)   │
│ ├─ Data Quality (Relational checks & warnings)         │
│ ├─ Imports (Excel/Form 460 ingestion logs)             │
│ ├─ Exports (Gephi GraphML & CSV downloads)             │
│ └─ Administration (System management)                  │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Workspace Walkthroughs

### Workflow 1: Dynamic Research Dashboard
* **Route**: `/research/`
* **Features**: Displays live counts of registered entities, documents, assertions, and transactions. Highlights unresolved duplicate candidates, active research tasks, open public records requests, and data-quality warning diagnostics. Includes a list of recently executed audits.

### Workflow 2: Unified Search Engine
* **Route**: `/search/`
* **Features**: Queries keywords across entity names, aliases, OCR page texts, assertion notes, transaction donor names, lobbying clients, contract vendors, and meeting agenda titles. Matches are grouped by type in the results layout. Includes a **Saved Search** action to preserve complex query parameters.

### Workflow 3: Browsable Entities Directory & Sorting
* **Route**: `/`
* **Features**: Features tabs to filter the directory (People, Organizations, Campaigns, Committees, Projects, Duplicates, and Recently Updated). Includes sorting links to sort by Name, Type, Status, Jurisdiction, or Date Updated.

### Workflow 4: Entity Profile Hub
* **Route**: `/entity/<public_id>/`
* **Features**: Interactive tab container compiling:
  - **Overview**: Core attributes and aliases.
  - **Timeline**: Chronological contributions, appointments, and contract awards. Features client-side checkbox filters to isolate event types.
  - **Assertions**: Documented relationships with direct links to source publication page ranges.
  - **Finance**: List of contributions made/received and expenditures.
  - **Lobbying**: Representation periods and compensation.
  - **Contracts & Projects**: Award amounts, execution dates, and planning project files.
  - **Government**: Observed legislative votes cast.
  - **Research & Duplicates**: Pinned portfolios and Jaro-Winkler Jaccard duplicate name candidates with merge actions.

### Workflow 5: Assertion Workbench
* **Route**: `/assertions/` (List), `/assertions/create/` (Create), `/assertions/edit/<uuid>/` (Edit)
* **Features**: Create or modify assertions using controlled vocabulary predicates. Features **Source Coordinate Highlighting** (auto-instantiating `SourceLocator` and `AssertionSource` links with page ranges and text excerpts).

### Workflow 6: Campaign Finance Ledgers
* **Route**: `/transactions/`
* **Features**: Filterable ledger supporting queries by donor name, recipient committee, cycle (year), minimum amount, and maximum amount.

### Workflow 7: Research Collections Workspace
* **Route**: `/research/collections/`
* **Features**: Group entities, sources, and transactions. Track tasks and PRA request logs inside the portfolio. Auto-seeds **"Muelrath Public Affairs"** tracking its specific members, tasks, and connections.

### Workflow 8: Unified Review Queue
* **Route**: `/extraction/queue/`
* **Features**: Review contributions, proposed matches, draft assertions, and provisional profiles.

### Workflow 9: Data-Quality Center & Bulk Actions
* **Route**: `/research/data-quality/`
* **Features**: Scans for blank jurisdictions, orphaned assertions, and duplicate FPPC committee IDs. Includes POST buttons to execute bulk corrections (e.g. assigning default jurisdictions to blank entries).

---

## 3. Dataset Exporters
* **Route**: `/exports/`
* **Features**: Direct download links for Canonical Entities CSV tables and Gephi-compatible Network GraphML files.

---

## 4. Verification and Reliability
* **Tests**: `pytest` validates all 16 integration tests successfully.
* **Checks**: `python manage.py check` passes with `0 errors`.
* **URLs Tested**: All 20 major endpoints respond with a successful **Status 200 (OK)** code.
