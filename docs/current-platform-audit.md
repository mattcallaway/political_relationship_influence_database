# Current Platform Audit: Sonoma County Political Relationship & Influence Database

This document presents a detailed audit of the platform's current Django application layers, database models, migrations, views, test coverage, and ingestion pipelines.

---

## 1. Application Layer Structure

The application is structured into the following specialized Django apps:

### 1. Core Platform & Domain Apps
* **`apps/entities`**: 
  - **Models**: `Entity`, `Person`, `Organization`, `Alias`, `PublicOffice`.
  - **Responsibilities**: Registers political actors, candidate profiles, corporate groups, government bodies, properties, and projects. Manages alternate name aliases, search indices, and directory list sorting.
* **`apps/campaigns`**:
  - **Models**: `Campaign`, `Committee`, `BallotMeasure`.
  - **Responsibilities**: Tracks election cycles, candidate campaign committees, and ballot measures.
* **`apps/transactions`**:
  - **Models**: `Contribution`, `Expenditure`, `Contract`, `LobbyingActivity`.
  - **Responsibilities**: Manages financial flows including campaign donations, vendor expenditures, government procurement contracts, and lobbying filings.
* **`apps/government`**:
  - **Models**: `Appointment`, `Meeting`, `AgendaItem`, `Motion`, `Vote`.
  - **Responsibilities**: Records local government bodies (e.g., Board of Supervisors), member appointments, meeting agendas, legislative motions, and individual supervisor votes.
* **`apps/projects`**:
  - **Models**: Implicitly uses `Entity` of type `DEVELOPMENT_PROJECT`.
  - **Responsibilities**: Manages real estate developments, public works projects, and associated planning/permitting processes.

### 2. Evidentiary & Provenance Apps
* **`apps/sources`**:
  - **Models**: `Source`, `SourceLocator`.
  - **Responsibilities**: Acts as the central registry for public files, reports, and news articles, and maps specific visual/page coordinates.
* **`apps/documents`**:
  - **Models**: `Document`, `DocumentPage`.
  - **Responsibilities**: Handles media file ingestion, PDF storage, text extraction (OCR), and page indexing.
* **`apps/assertions`**:
  - **Models**: `Assertion`, `AssertionSource`, `PredicateVocabulary`.
  - **Responsibilities**: Represents factual claims or relationship edges linking entities, backed by source locators.

### 3. Investigation & Operations Apps
* **`apps/research`**:
  - **Models**: `ResearchCollection`, `ResearchTask`, `OpenQuestion`, `PRARequest`, `SavedSearch`.
  - **Responsibilities**: Supports research folders (collections), task checklists, outstanding investigator questions, and public records request tracking.
* **`apps/extraction`**:
  - **Models**: `ExtractedField`, `ExtractedContributorBlock`, `EntityMatchAttempt`, `EntityMatchCandidate`.
  - **Responsibilities**: Houses Form 460 OCR segmentation, Jaro-Winkler Jaccard entity matching algorithms, and the unified review queue.
* **`apps/audit`**:
  - **Models**: `LegacyIdentifier`, `ImportBatch`.
  - **Responsibilities**: Records Excel migration imports, parser versions, and system synchronization logs.

---

## 2. Views & URL Configuration Audit

A unified global routing configuration maps views across apps:
* **Global Navbar Navigation**: Configured in `templates/base.html` to link to all major dashboards, search views, and ledgers.
* **Dashboard (`/research/`)**: Displays diagnostic status metrics, unresolved matches, open tasks, and recent audit trails.
* **Unified Search (`/search/`)**: Implements query parsing across entity names, OCR text, transactions, contracts, and meeting agendas.
* **Review Queue (`/extraction/queue/`)**: Displays auto-extracted contributions, match candidates, and unapproved assertions.
* **Network Explorer & Path Compare (`/research/network/`, `/research/compare/`)**: Visualizes Cytoscape relationships and direct/indirect path links.
* **Data-Quality Center (`/research/data-quality/`)**: Logs integrity warnings and provides POST endpoints for bulk changes.
* **Export Center (`/exports/`)**: Generates CSV and Gephi GraphML output files.

---

## 3. Test Coverage & Diagnostics Audit

* **Test Suite**: Located in the `tests/` directory:
  - `test_entity_merge.py`: Validates entity merge and rollback.
  - `test_fppc460_extraction.py`: Audits OCR field parsing and bounding boxes.
  - `test_generic_parsers.py`: Asserts correctness of document ingestion.
  - `test_ingestion_cataloging.py`: Checks file scanning and cataloging.
  - `test_milestone1.py`: Confirms page layouts and initial structures.
* **Test Health**: All **16/16 tests pass cleanly** in 8.34s using SQLite.
* **System Checks**: Running `python manage.py check` reports `0 errors`.
* **Migrations**: `python manage.py showmigrations` confirms all migrations across the 13 apps have been fully applied.

---

## 4. Operational Gaps

* **Campaign Expenditures**: The database models have an initial `Expenditure` schema, but it lacks a Schedule E parser, generic CSV importer, campaign vendor profile pages, and comprehensive UI list/detail workbenches.
* **Data Quality Scope**: The diagnostics scan checks for basic errors but lacks automated checkers for invalid monetary limits, impossible appointment dates, alias incompatibilities, and conflicting assertions.
* **Missing Seed Data**: The Muelrath Public Affairs collection is auto-seeded dynamically but requires richer links to campaigns, expenditures, vendors, and lobbying activities to show a complete relationship map.
