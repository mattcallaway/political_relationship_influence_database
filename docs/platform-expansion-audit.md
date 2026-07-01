# Platform Expansion Audit: Sonoma Civic Research Platform

This document presents a comprehensive review of the current database models, Django migrations, Form 460 Schedule A extraction pipeline, and excel workbook v5 schemas. It identifies structural assets, migration risks, and design choices necessary to scale the platform from campaign-finance tracking into a unified, evidence-centered political influence database.

---

## 1. Models Analysis

### Shared Platform Infrastructure Candidates
The following models are already architected to serve as generic infrastructure across the whole application:
* **`Source` (`apps/sources/models.py`)**: Can become the centralized registry for news articles, agendas, staffing reports, minutes, contracts, and PRA responses.
* **`Document` & `DocumentPage` (`apps/documents/models.py`)**: Already handle media preservation, hashes, native text checks, and page extraction cleanly.
* **`Entity` (`apps/entities/models.py`)**: Acts as the universal registry for all political actors. Its status fields can scale to support public/private visibility and matching categories.
* **`Alias` (`apps/entities/models.py`)**: Handles alternate name lists.
* **`Assertion` & `AssertionSource` (`apps/assertions/models.py`)**: Serve as the core graph edge registry mapping claims to source documents.
* **`AuditEvent` (`apps/transactions/models.py`)**: Records full historical values for audit transparency.

### Schedule A Specific Models
The following models are tightly coupled to California Form 460 Schedule A and must remain isolated to the campaign finance ingestion pipeline:
* **`ExtractedField` & `ExtractedContributorBlock` (`apps/extraction/models.py`)**: Hold geometry bounding boxes, raw OCR text chunks, and validation ratings specific to Form 460 grids.
* **`EntityMatchAttempt` & `EntityMatchCandidate` (`apps/extraction/models.py`)**: Store scores (name, location, employer) and candidate alternatives specific to contributor name searches.

---

## 2. Structural Duplications and Inconsistencies

* **Duplicate Notes Fields**: `notes` columns exist on `Entity`, `Person`, and `Organization`. These should be unified (e.g., entity-level general description versus personal biographical details).
* **FPPC ID Identification**: FPPC IDs are stored as `committee_id` in `Organization` and `FPPCID` in the workbook. These must be normalized to a standard field in a dedicated `Committee` subtype model to support campaigns, expenditures, and contributions uniformly.
* **Redundant Jurisdiction Fields**: `jurisdiction` is stored across `Person`, `Organization`, and `Campaign`, as well as on `Source` records. Jurisdiction is logically a property of the *governmental body* or *source filing scope* rather than individual profiles.
* **Raw vs. Canonical Name Drift**: `Contribution` stores `donor_raw_name`, but when auto-matching links the transaction to a canonical `Entity`, the canonical name should be retrieved from the entity rather than duplicate columns.

---

## 3. Migration Risks & Potential Data Loss

* **Choices Expansion & Enforceability**: Redefining choices for `Entity.status` and `Contribution.review_status` will trigger validation crashes for existing records using the old `'PROPOSED'` or `'APPROVED'` choices. Data migrations must run first to map:
  - `PROPOSED` (Entity) $\rightarrow$ `PROVISIONAL_AUTO_CREATED`
  - `APPROVED` (Entity) $\rightarrow$ `VERIFIED`
  - `PROPOSED` (Contribution) $\rightarrow$ `AUTO_IMPORTED`
  - `APPROVED` (Contribution) $\rightarrow$ `VERIFIED`
* **Column Length Constraints**: `Entity.status` was updated to `max_length=50`, but other status fields (like `Alias.review_status` or `Document.processing_status`) have narrower limits that could truncate incoming status text.
* **Cascading Deletions**: Deleting an `Entity` or `Document` might cascade and delete all associated `Contribution` or `AuditEvent` records, causing critical data loss. Foreign keys must use `on_delete=models.PROTECT` or `on_delete=models.SET_NULL` where auditability is required.

---

## 4. Missing Provenance, Constraints, & Indexes

* **Visual Provenance (Source Locators)**: Currently, `Contribution` and `Assertion` point directly to a page or document, but lack a `SourceLocator` model to map visual coordinates, line items, agenda item numbers, and PDF tables.
* **Unique Constraints**:
  - `Alias` needs a unique constraint on `(entity, alias_text)` to prevent duplicate name registrations on a single entity profile.
  - `LegacyIdentifier` needs unique constraints on `(originating_system, legacy_id)` to keep mappings idempotent.
* **Database Indexes**:
  - Add indexes on foreign keys: `Contribution.donor_entity`, `Contribution.filer_committee`, `AuditEvent.record_id`.
  - Add indexes on lookup text fields: `Alias.normalized_alias`, `Entity.canonical_name`.
