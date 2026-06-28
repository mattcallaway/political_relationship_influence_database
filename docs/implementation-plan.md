# Technical Implementation Plan
**Project Name**: Sonoma Political Relationship and Influence Database  
**Author**: Lead Architect & Implementation Engineer  
**Branch**: `feature/initial-research-platform`  
**Date**: June 2026  

---

## 1. Executive Summary & Core Mission
The Sonoma Political Relationship and Influence Database is an open, auditable research platform engineered for ingesting, reviewing, categorizing, preserving, and analyzing public records concerning political campaigns, lobbying, government decisions, campaign finance, organizations, and public officials in Sonoma County, California.

### Non-Negotiable Research Principles
1. **Preserve original documents & page provenance**: Store SHA-256 hashes for all uploaded documents and never modify raw uploads.
2. **Separation of machine extraction & authoritative verification**: OCR output and extracted fields remain in staging until explicitly reviewed and approved.
3. **No automatic entity merging**: Fuzzy entity matches present scores and recommendations, but canonical entity merges require authorized human approval.
4. **Distinguish facts from interpretations**: Claims are strictly classified into `factual`, `interpretive`, `allegation`, `hypothesis`, and `context`.
5. **Privacy and Redaction**: Redact bank account numbers, signatures, personal phone numbers, and home addresses where legally appropriate.

---

## 2. Risk Register & Mitigation Strategies

| Risk ID | Risk Description | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **RISK-01** | OCR misreads Form 460 Schedule A numbers or names | **High** | Mandatory side-by-side human review UI; raw OCR text retained separately from verified fields. |
| **RISK-02** | Silent duplicate entity creation during batch import | **High** | Conservative matching engine using exact committee IDs, known aliases, and legacy mapping tables. |
| **RISK-03** | Unauthorized exposure of sensitive or private data | **Critical** | Dynamic field redaction in serializers; multi-tiered RBAC (Researcher vs. Reviewer vs. Admin). |
| **RISK-04** | Loss of original document provenance | **Critical** | Immutable file storage abstraction; mandatory SHA-256 hash checking upon upload. |

---

## 3. Technology Stack & Architecture

### Backend
- **Framework**: Python 3.12+ / Django 5.x / Django REST Framework
- **Database**: PostgreSQL with `psycopg3` driver
- **Asynchronous Processing**: Celery with Redis broker
- **Data Validation & Extraction**: Pydantic & PyMuPDF (fitz) / Tesseract OCR / OCRmyPDF

### Frontend & User Interface
- **Architecture**: Django Server-Side Templates + HTMX + Vanilla CSS design system
- **Aesthetics**: Dark-mode compatible, sleek glassmorphism, accessible semantic HTML, responsive layout tailored for desktop research workflows.

### Modular Application Structure (`apps/`)
- `apps/accounts/`: Custom User model and Role-Based Access Control (RBAC).
- `apps/entities/`: Base `Entity`, `Person`, `Organization`, `Alias` models.
- `apps/sources/`: `Source` metadata, reliability classifications, jurisdiction catalog.
- `apps/documents/`: Immutable file storage, `Document`, `DocumentPage` models.
- `apps/extraction/`: `ExtractionJob`, `ExtractedField`, Form 460 parsing routines.
- `apps/assertions/`: Evidentiary assertions (`Assertion`) and source links (`AssertionSource`).
- `apps/campaigns/`: Committees, candidates, ballot measures.
- `apps/transactions/`: Financial records (`Contribution`, `Expenditure`, `Loan`, `Contract`, `LobbyingActivity`).
- `apps/government/`: `PublicOffice`, `GovernmentBody`, `Vote`, `Appointment`.
- `apps/projects/`: Land development and civic infrastructure projects (`Project`).
- `apps/research/`: `IntakeItem`, `ResearchTask`, `PRARequest`, `DataQualityIssue`.
- `apps/audit/`: System-wide audit log (`ChangeLog`) and `ControlledVocabularyValue`.
- `apps/exports/`: Network and dataset exporters (CSV, XLSX, GraphML, JSON).

---

## 4. Implementation Sequence by Stages

### Stage 1: Inspection, Auditing & Architecture Plan
- [x] Repository and directory inspection.
- [x] Seed XLSX workbook audit and mock generation.
- [x] Produce `docs/v5-workbook-schema-audit.md` and `docs/implementation-plan.md`.

### Stage 2: Core Platform Scaffolding & Domain Schema
- Docker Compose, PostgreSQL, Django settings, and apps initialization.
- Base models: `Entity`, `Person`, `Organization`, `Alias`, `Source`, `Assertion`, `Contribution`, `Expenditure`.
- Idempotent v5 Workbook Importer (`python manage.py import_v5_workbook`).

### Stage 3: Immutable Storage & Document Ingestion Pipeline
- Document model, SHA-256 hashing, duplicate file warnings.
- Born-digital PDF extraction via PyMuPDF.
- Celery background job queue for async processing.

### Stage 4: Form 460 Parser & Side-by-Side Human Review UI
- Specialized extractor for FPPC Form 460 cover page, Schedule A, and Schedule E.
- HTMX side-by-side review screen with document page viewer on left and verification form on right.
- Conservative entity resolution candidate scoring.

### Stage 5: Research Interfaces, Entity Detail & Graph Exports
- Unified multi-model search interface.
- Rich Entity Detail page featuring identity tabs, financial timelines, and verified assertions.
- Data exporters (CSV, XLSX, JSON, GraphML for Gephi).

### Stage 6: Documentation, Testing & Acceptance Validation
- Complete end-to-end pytest suite and browser smoke test.
- Comprehensive README.md and supporting governance docs.

---

## 5. Verification & Acceptance Criteria
- Full compliance with Milestone 1 acceptance steps.
- Clean execution of tests via `pytest`.
- Successful dry-run and live import of the v5 workbook.
