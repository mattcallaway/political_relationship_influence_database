# Sonoma Political Relationship and Influence Database

## 1. Project Title and Summary
**Sonoma Political Relationship and Influence Database** is an open, auditable research application engineered for ingesting, reviewing, categorizing, preserving, and analyzing public records concerning political campaigns, lobbying, government decisions, appointments, development projects, campaign finance, organizations, consultants, donors, and public officials in Sonoma County, California.

## 2. Statement of Purpose
The purpose of this application is to support rigorous, evidence-centered public-interest research into municipal and county political ecosystems. It establishes an auditable infrastructure connecting every factual assertion directly to supporting public-record provenance.

## 3. Public-Interest Rationale
Civic transparency relies on accessible, traceable public records. Campaign finance filings (Form 460), lobbying disclosures, board meeting minutes, and property development records are often fragmented across disparate government portals. This database consolidates these records into a unified, searchable platform while maintaining strict evidentiary standards.

## 4. What the Project Does
- Ingests California campaign-finance disclosures (Form 460, 410, 496, 497).
- Preserves original uploaded PDFs and documents with immutable SHA-256 hashing.
- Extracts text layers and runs OCR preprocessing for scanned historical filings.
- Provides a side-by-side human verification review interface.
- Resolves entity names conservative to prevent duplicate canonical record creation.
- Exports structured datasets to CSV, XLSX, JSON, and Gephi GraphML formats.

## 5. What the Project Explicitly Does Not Claim or Do
- **Does not accuse individuals or organizations of wrongdoing** merely because they have documented political, financial, or professional connections.
- **Does not compute simplistic "corruption scores" or "influence metrics."**
- **Does not automatically publish machine-extracted OCR values** without human verification.
- Documented association does not inherently demonstrate influence, coordination, or impropriety.

## 6. Research and Evidentiary Principles
1. **Preserve original documents**: Original raw files are preserved unaltered.
2. **Page provenance**: Every claim links to exact document page locators.
3. **Never overwrite source data**: Extracted fields remain in staging until reviewed.
4. **Retain conflicting evidence**: Contradicting records remain visible for review.

## 7. Explanation of Facts vs. Interpretations vs. Hypotheses
All assertions are explicitly typed into one of five categories:
- `FACTUAL`: Direct public record entries (e.g. contribution date/amount).
- `INTERPRETIVE`: Analytic interpretations by researchers.
- `ALLEGATION`: Formal inquiry claims.
- `HYPOTHESIS`: Working research leads.
- `CONTEXT`: Historical background context.

## 8. Data Model Overview
The system utilizes normalized Django apps (`accounts`, `entities`, `sources`, `documents`, `extraction`, `assertions`, `campaigns`, `transactions`, `government`, `projects`, `research`, `audit`, `exports`).

## 9. Assertions and Source Provenance
`Assertion` records connect a subject entity to a predicate and object value, backed by `AssertionSource` links to specific document pages.

## 10. Form 460 Ingestion Workflow
Supports Form 460 cover page, Schedule A (Contributions), and Schedule E (Expenditures) with structured parser mapping.

## 11. General Document Ingestion Workflow
Non-460 documents (minutes, staff reports, contracts, PRAs) undergo upload classification, SHA-256 hashing, text extraction, and manual highlighting.

## 12. Human-Review and Status Requirements
The central database contains records at different stages of confidence and review. Automatic matching is used to make incoming filings immediately useful. Review status, provenance, confidence, and audit history allow users to distinguish provisional machine-assisted records from human-verified records. Reviewers confirm, correct, rematch, merge, split, or reject records directly inside the central database, leaving a complete audit trail.

## 13. Entity Resolution and Duplicate Handling
Conservative fuzzy matching scores recommendations but strictly requires human review for entity merges. Merges preserve legacy IDs as aliases.

## 14. Controlled Vocabularies
Standardized taxonomies stored in `ControlledVocabularyValue` govern entity types, org categories, predicates, and claim types.

## 15. Audit Trail
All edits, entity merges, and verification decisions are logged in `ChangeLog` and `ReviewDecision`.

## 16. Privacy, Ethics, and Responsible Use
Redacts bank account numbers, signatures, personal phone numbers, and home addresses where legally appropriate.

## 17. Current Limitations
Milestone 1 implements single-layout Form 460 parsing and conservative heuristic entity matching. Advanced multi-layout parser modules are planned for Milestone 2.

## 18. Technology Architecture
- Backend: Python 3.12, Django 6.0, Django REST Framework, PostgreSQL, Celery, Redis.
- Frontend: Django Templates, HTMX, Vanilla CSS design system.
- Extraction: PyMuPDF, pypdf, Tesseract OCR.

## 19. Repository Layout
Organized cleanly into `apps/`, `config/`, `docs/`, `scripts/`, `tests/`, `templates/`, `static/`, and `data/`.

## 20. Local Prerequisites
- Python 3.12+
- PostgreSQL & Redis (or Docker Compose)

## 21. Installation Instructions
```bash
git clone https://github.com/mattcallaway/political_relationship_influence_database.git
cd political_relationship_influence_database
python -m venv venv
venv\Scripts\activate
pip install -r pyproject.toml (or pip install django djangorestframework psycopg openpyxl pymupdf pypdf celery redis pytest pytest-django)
```

## 22. Docker Compose Instructions
```bash
docker-compose up --build -d
```

## 23. Environment Variables Reference
Refer to `.env.example` for `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, and `DEBUG`.

## 24. Database Creation and Migration Steps
```bash
python manage.py makemigrations
python manage.py migrate
```

## 25. V5 Workbook Import Instructions
```bash
python manage.py import_v5_workbook --file data/imports/Sonoma_Political_Influence_Database_v5_consolidated.xlsx
```

## 26. Test Commands
```bash
pytest
```

## 27. Linting Commands
```bash
ruff check .
```

## 28. Background Worker Instructions
```bash
celery -A config worker -l info
```

## 29. OCR Dependencies Setup
Install Tesseract OCR locally and ensure `tesseract` is on PATH.

## 30. Troubleshooting
Check `.env` database settings and Celery worker connectivity.

## 31. Backup and Restore
Use `pg_dump` and `pg_restore` for production PostgreSQL backups.

## 32. Data Export Procedures
Access `/exports/` for CSV table downloads and GraphML network exports.

## 33. Development Workflow
Feature branches (`feature/name`), small commits, pytest verification prior to PRs.

## 34. Branch and Commit Conventions
Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`).

## 35. How to Contribute
See `CONTRIBUTING.md`.

## 36. Reporting Data Corrections
Refer to `docs/corrections-policy.md`.

## 37. Proposing Schema Changes
Submit an RFC issue or documentation update in `docs/schema.md`.

## 38. Security Reporting
See `SECURITY.md`.

## 39. Roadmap
Milestone 2: Multi-layout Form 460 parser, automated PRA response parsing, interactive D3 network visualizer.

## 40. License Status
Refer to `LICENSE-TODO.md`.

## 41. Governance
Project maintained by civic public-interest researchers.

## 42. Glossary
- **Form 460**: FPPC Recipient Committee Campaign Statement.
- **PRA**: Public Records Act request.
- **Entity**: Canonical person or organization record.

## 43. Acknowledgment
Documented political, financial, or professional association does not by itself demonstrate influence, coordination, corruption, or wrongdoing.
