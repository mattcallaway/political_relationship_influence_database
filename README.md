# Sonoma County Political Relationship & Influence Database

## Civic-Research Mission & Statement of Purpose
The Sonoma County Political Relationship & Influence Database is an open, auditable research platform engineered for organizing public records and documenting political, financial, governmental, professional, business, and civic relationships. 

Its primary purpose is to help researchers, journalists, and the public map how campaigns, public officials, private firms, contracts, boards, appointments, lobbying registries, and votes connect over time. The platform establishes a structured, evidence-backed workspace where every connection is tied directly to page-level public record evidence.

> [!IMPORTANT]
> **Non-Judgmental Representation**: The existence of a documented political, financial, professional, or board connection does not inherently demonstrate improper influence, coordination, conflict of interest, or wrongdoing. The system presents evidence of relationships; normative interpretation remains the role of the researcher.

---

## Project Architecture

The database is built on a structured hierarchy of evidence, cataloged actors, public actions, and research layers, described in the following sequence:

### 1. Sources and Evidence
At the foundation of all records are original, unaltered source documents (PDFs, spreadsheets, minutes, filings).
- **Document Integrity**: Original documents are preserved with unique SHA-256 hashes.
- **Granular Provenance**: Page-level references (`SourceLocator`) track exactly where data originates in the original document.

### 2. Canonical Entities
Uniquely identified nodes representing actors inside the political and civic ecosystem.
- **Entity Types**: Standardized profiles (`PERSON`, `ORGANIZATION`, `COMMITTEE`, `COMPANY`).
- **Entity States**: Separation of `VERIFIED` profiles, `AUTO_MATCHED` suggestions, and unverified `PROVISIONAL_AUTO_CREATED` profiles.
- **Merge History**: Aliases and legacy IDs are fully preserved during entity merges.

### 3. Structured Transactions and Public Actions
Standardized transactional and operational records linked directly to entities and source locators.
- **Campaign Finance**: Contributions (FPPC Form 460 Schedule A) and expenditures (FPPC Form 460 Schedule E).
- **Government Operations**: Appointments, board structures, meetings, agenda items, motions, and individual roll-call votes.
- **Professional Services**: Public contracts, lobbying activity reports, and consulting networks.

### 4. Assertions and Review
Research claims and verification workflows that model data confidence and accuracy.
- **Claims Categorization**: Assertions are categorized by status (`FACTUAL`, `INTERPRETIVE`, `HYPOTHESIS`, `ALLEGATION`).
- **Verification States**: Links remain reviewable as `PROPOSED`, `REVIEWED`, `VERIFIED`, or `DISPUTED`.
- **Review Queues**: Human-in-the-loop interfaces to confirm automatic match recommendations, reconcile duplicates, and verify extraction suggestions.

### 5. Research Collections and Investigation
Investigation workspaces that function as command centers for specific subjects (e.g. Muelrath Public Affairs).
- **Consolidated Dashboards**: Displays all connected actors, financials, contracts, and appointments.
- **Research Gaps**: Missing categories are shown explicitly as gaps rather than being hidden.
- **Inquiry Logs**: Track tasks and open research questions connected directly to actors and files.

### 6. Timelines and Networks
Visual and chronological projections of database data.
- **Timeline overlapping**: Chronological overlapping of contributions, contracts, votes, and lobbying filings.
- **Evidence Network Explorer**: Direct graph projections where every edge displays its origin record ID, status, and source count.

### 7. Ingestion Adapters
Supporting input adapters that populate the central schemas.
- **Form 460 Adapter**: Visual 2D coordinate-based parser extracting Schedule A transactions and checkboxes.
- **OCR Pipeline**: Text extraction and OCR preprocessing supporting search on scanned historical documents.

### 8. Operations and Governance
System administration and data safety routines.
- **Backups**: Management commands validating SQLite integrity (`PRAGMA integrity_check`) before saving timestamped copies.
- **Batch Rollback**: Management commands to revert and clean up imported batches safely.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.12+
- SQLite (default) or PostgreSQL

### 2. Installation
```bash
git clone https://github.com/mattcallaway/political_relationship_influence_database.git
cd political_relationship_influence_database
python -m venv venv
venv\Scripts\activate
pip install -r pyproject.toml
```

### 3. Database Creation and Migrations
```bash
$env:USE_SQLITE="True"
python manage.py makemigrations
python manage.py migrate
```

### 4. Running the Development Server
```bash
$env:USE_SQLITE="True"
python manage.py runserver
```

### 5. Run Automated Tests
```bash
$env:USE_SQLITE="True"
pytest
```
