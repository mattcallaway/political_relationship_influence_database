# Target Domain Model: Sonoma Civic Research Platform

This document specifies the target relational domain model for the expanded Sonoma County Political Influence Database. The schema is organized into five logical layers.

---

## Layer 1: Sources and Documents

Handles original document files, OCR text extractions, and visual coordinates references.

```
Source
├── id (UUID, PK)
├── public_id (Char, unique e.g. SRC000001)
├── title (Char)
├── source_type (Char, choices)
├── issuing_body (Char)
├── author (Char)
├── publication_date (Date)
├── filing_date (Date)
├── access_date (Date)
├── original_url (URL)
├── archive_url (URL)
├── jurisdiction (Char)
├── reliability (Char, choices)
├── privacy_classification (Char, choices)
├── notes (Text)
├── created_at (DateTime)
└── updated_at (DateTime)

Document
├── id (UUID, PK)
├── public_id (Char, unique e.g. DOC000001)
├── source (FK Source, null)
├── original_filename (Char)
├── file_path (File)
├── media_type (Char)
├── byte_size (BigInt)
├── sha256_hash (Char, unique)
├── page_count (Int)
├── upload_user (FK User, null)
├── uploaded_at (DateTime)
├── has_native_text (Bool)
├── ocr_applied (Bool)
├── processing_status (Char, choices)
└── publication_classification (Char, choices)

DocumentPage
├── id (UUID, PK)
├── document (FK Document)
├── page_number (Int)
├── extracted_text (Text)
├── ocr_text (Text)
├── ocr_confidence (Float)
├── page_image (Image)
├── page_width (Float)
├── page_height (Float)
├── processing_status (Char)
└── review_status (Char)

SourceLocator
├── id (UUID, PK)
├── source (FK Source)
├── document (FK Document, null)
├── page (FK DocumentPage, null)
├── page_range (Char)
├── bounding_box_json (JSON, e.g. [vx0, vy0, vx1, vy1])
├── section (Char)
├── table_identifier (Char)
├── agenda_item (Char)
├── filing_schedule (Char)
└── locator_description (Text)
```

---

## Layer 2: Canonical Entities

Uses a single universal `Entity` table for graph connectivity, with one-to-one subtype tables for domain-specific metadata.

```
Entity
├── id (UUID, PK)
├── public_id (Char, unique e.g. ENT000001)
├── entity_type (Char, choices: PERSON, ORGANIZATION, CAMPAIGN, COMMITTEE, BALLOT_MEASURE, PROJECT, GOVT_BODY, OFFICE, PROPERTY, CONTRACT, EVENT, OTHER)
├── canonical_name (Char, index)
├── normalized_name (Char, index)
├── status (Char, choices: PROVISIONAL_AUTO_CREATED, AUTO_MATCHED, NEEDS_REVIEW, REVIEWED, VERIFIED, MERGED, REJECTED, ARCHIVED)
├── publication_status (Char, choices)
├── jurisdiction (Char)
├── created_at (DateTime)
└── updated_at (DateTime)

Person (Subtype)
├── entity (OneToOne Entity, PK)
├── given_name (Char)
├── middle_name (Char)
├── family_name (Char)
├── suffix (Char)
├── display_name (Char)
├── public_role (Char)
├── occupation (Char)
└── notes (Text)

Organization (Subtype)
├── entity (OneToOne Entity, PK)
├── legal_name (Char)
├── common_name (Char)
├── organization_category (Char, choices)
├── fppc_committee_id (Char)
├── state_business_id (Char)
├── active_status (Bool)
├── formation_date (Date)
└── dissolution_date (Date)

Campaign (Subtype)
├── entity (OneToOne Entity, PK)
├── candidate (FK Entity, Person)
├── office (FK Entity, PublicOffice)
├── election_date (Date)
├── election_cycle (Char)
├── jurisdiction (Char)
├── committee (FK Entity, Committee, null)
├── campaign_status (Char)
└── outcome (Char)

Committee (Subtype)
├── entity (OneToOne Entity, PK)
├── fppc_id (Char)
├── committee_type (Char)
├── controlling_candidate (FK Entity, Person, null)
├── sponsor (FK Entity, Organization, null)
└── active_status (Bool)

BallotMeasure (Subtype)
├── entity (OneToOne Entity, PK)
├── measure_number (Char)
├── title (Char)
├── election_date (Date)
├── jurisdiction (Char)
└── result (Char)

Project (Subtype)
├── entity (OneToOne Entity, PK)
├── project_category (Char)
├── jurisdiction (Char)
├── application_number (Char)
├── location (Char)
├── applicant (FK Entity, null)
├── property_owner (FK Entity, null)
├── status (Char)
├── start_date (Date)
└── end_date (Date)

GovernmentBody (Subtype)
├── entity (OneToOne Entity, PK)
├── body_type (Char)
├── jurisdiction (Char)
└── parent_body (FK Entity, GovernmentBody, null)

PublicOffice (Subtype)
├── entity (OneToOne Entity, PK)
├── office_name (Char)
├── district (Char)
├── jurisdiction (Char)
└── elected_or_appointed (Char)

Alias
├── id (UUID, PK)
├── entity (FK Entity)
├── alias_text (Char)
├── normalized_alias (Char)
├── alias_type (Char)
├── effective_start (Date)
├── effective_end (Date)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

LegacyIdentifier
├── id (UUID, PK)
├── entity (FK Entity)
├── originating_system (Char)
├── legacy_id (Char)
├── source_workbook (Char)
└── import_batch (FK ImportBatch, null)
```

---

## Layer 3: Transactions and Public Actions

Structured connections containing transaction amounts, codes, and vote selections.

```
Contribution
├── id (UUID, PK)
├── public_id (Char, unique)
├── filer_committee (FK Entity, Committee)
├── donor_entity (FK Entity)
├── donor_raw_name (Char)
├── transaction_date (Date)
├── amount (Decimal)
├── cumulative_amount (Decimal)
├── schedule (Char)
├── transaction_code (Char)
├── occupation (Char)
├── employer (Char)
├── city_state_zip (Char)
├── source_locator (FK SourceLocator, null)
├── extracted_block (FK ExtractedContributorBlock, null)
├── review_status (Char)
└── superseded_by (FK 'self', null)

Expenditure
├── id (UUID, PK)
├── public_id (Char, unique)
├── paying_committee (FK Entity, Committee)
├── payee_entity (FK Entity)
├── payee_raw_name (Char)
├── transaction_date (Date)
├── amount (Decimal)
├── purpose_code (Char)
├── description (Text)
├── candidate_measure (FK Entity, null)
├── agent_subcontractor (FK Entity, null)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

Contract
├── id (UUID, PK)
├── public_id (Char, unique)
├── contracting_body (FK Entity, GovernmentBody)
├── contractor (FK Entity)
├── contract_number (Char)
├── award_date (Date)
├── start_date (Date)
├── end_date (Date)
├── amount (Decimal)
├── purpose (Text)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

LobbyingActivity
├── id (UUID, PK)
├── lobbying_entity (FK Entity)
├── client (FK Entity)
├── government_body (FK Entity, GovernmentBody)
├── reporting_period (Char)
├── matter_description (Text)
├── compensation (Decimal)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

Appointment
├── id (UUID, PK)
├── appointee (FK Entity, Person)
├── appointing_body (FK Entity)
├── appointed_office (FK Entity, PublicOffice)
├── appointment_date (Date)
├── term_start (Date)
├── term_end (Date)
├── term_status (Char)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

Meeting
├── id (UUID, PK)
├── government_body (FK Entity, GovernmentBody)
├── date (Date)
├── location (Char)
├── agenda_source (FK Source, null)
└── minutes_source (FK Source, null)

AgendaItem
├── id (UUID, PK)
├── meeting (FK Meeting)
├── item_number (Char)
├── title (Char)
├── description (Text)
├── related_project (FK Entity, Project, null)
├── staff_recommendation (Char)
└── outcome (Char)

Motion
├── id (UUID, PK)
├── agenda_item (FK AgendaItem)
├── motion_text (Text)
├── mover (FK Entity, Person, null)
├── seconder (FK Entity, Person, null)
└── result (Char)

Vote
├── id (UUID, PK)
├── motion (FK Motion)
├── voting_member (FK Entity, Person)
├── vote_value (Char, choices: AYE, NAY, ABSTAIN, RECUSE, ABSENT)
├── recusal_reason (Text)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

PublicComment
├── id (UUID, PK)
├── agenda_item (FK AgendaItem)
├── speaker (FK Entity, Person)
├── represented_organization (FK Entity, Organization, null)
├── position (Char, choices: SUPPORT, OPPOSE, NEUTRAL)
├── summary (Text)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)

ProjectAction
├── id (UUID, PK)
├── project (FK Entity, Project)
├── government_body (FK Entity, GovernmentBody)
├── action_type (Char)
├── date (Date)
├── outcome (Char)
├── source_locator (FK SourceLocator, null)
└── review_status (Char)
```

---

## Layer 4: Assertions and Evidence

Registers directional relationship graphs between entities. Factual claims point to backing sources, separating researcher interpretations from observable transactions.

```
Assertion
├── id (UUID, PK)
├── public_id (Char, unique e.g. AST000001)
├── subject_entity (FK Entity)
├── predicate (Char, index)
├── object_entity (FK Entity, null)
├── object_value (Char, null)
├── claim_type (Char, choices: FACTUAL, INTERPRETIVE, ALLEGATION, HYPOTHESIS, CONTEXT)
├── verification_status (Char, choices: LEAD, UNVERIFIED, PARTIALLY_VERIFIED, VERIFIED, DISPUTED, SUPERSEDED, RETRACTED)
├── confidence_score (Float)
├── effective_start (Date)
├── effective_end (Date)
├── jurisdiction (Char)
├── interpretation_required (Bool)
├── sensitive_claim (Bool)
├── publication_status (Char)
├── explanatory_note (Text)
├── created_by (FK User)
├── reviewed_by (FK User, null)
└── review_date (DateTime)

AssertionSource
├── id (UUID, PK)
├── assertion (FK Assertion)
├── source_locator (FK SourceLocator)
├── support_type (Char, choices: PRIMARY, CORROBORATING, CONTRADICTING, CONTEXTUAL)
├── evidence_note (Text)
└── reviewer (FK User, null)
```

---

## Layer 5: Research Operations

Handles research assignments, collections, matching logs, and duplicate merges.

```
ResearchCollection
├── id (UUID, PK)
├── name (Char)
├── description (Text)
├── entities (ManyToMany Entity)
├── sources (ManyToMany Source)
├── contributions (ManyToMany Contribution)
├── assertions (ManyToMany Assertion)
├── created_at (DateTime)
└── created_by (FK User)

ResearchTask
├── id (UUID, PK)
├── priority (Char)
├── title (Char)
├── description (Text)
├── assigned_to (FK User, null)
├── due_date (Date)
├── status (Char)
└── entity (FK Entity, null)

PRARequest
├── id (UUID, PK)
├── agency (FK Entity, GovernmentBody)
├── title (Char)
├── summary (Text)
├── date_submitted (Date)
├── status (Char)
└── notes (Text)
```
