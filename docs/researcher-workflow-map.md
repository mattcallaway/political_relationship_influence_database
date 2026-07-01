# Researcher Workflow Map

This document outlines the core workflows and user paths for researchers, reviewers, and administrators operating in the Sonoma County Political Relationship & Influence Database workspace.

---

## 1. User Roles & Permission Matrices

The platform divides responsibilities across distinct tiers of authorization to protect the audit trail:

```
┌────────────────────────────────────────────────────────┐
│                     ADMINISTRATOR                      │
│ (All Actions, Vocabulary Management, publication control)│
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│                   RESEARCH MANAGER                     │
│ (Assign tasks, approve sensitive claims, bulk actions)  │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│                       REVIEWER                         │
│ (Verify/dispute/correct records, confirm/rematch links)│
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│                      RESEARCHER                        │
│ (Create provisional items, upload docs, add assertions) │
└────────────────────────────────────────────────────────┘
```

---

## 2. Core Workspace Workflows

### Workflow 1: Document Upload, Classification & Extraction
1. **Intake**: A **Researcher** uploads a raw PDF or CSV filing through the Ingestion Workspace.
2. **Hashing & Classify**: System checks the SHA-256 hash to prevent duplicate uploads, runs the generic document classifier (Form 460, Minutes, Lobbying), and attaches a newly created `Source` record.
3. **OCR & Parse**: The system parses the file page-by-page. For Form 460 and Minutes, it extracts structured contributors, motions, and votes into provisional/auto-matched records.
4. **Queue**: Extracted records are staged directly in the central database with `AUTO_IMPORTED` or `AUTO_MATCHED` status and routed to the **Review Queue**.

---

### Workflow 2: Transaction Matching & Review Queue
1. **Inspection**: A **Reviewer** opens the Review Queue, filtering by type (e.g. `Contribution`).
2. **Side-by-Side Review**: The reviewer examines the parsed block raw text alongside the auto-matched canonical Entity.
3. **Decide**:
   - **Confirm Match**: The reviewer verifies the auto-link is correct. The system updates status to `REVIEWER_CONFIRMED` and logs an `AuditEvent`.
   - **Rematch**: The reviewer overrides the link, select a different entity, or creates a new canonical entity. System updates the link and stores the original match in history.
   - **Correct**: The reviewer fixes spelling errors or monetary values, triggering an audit record of changed fields.

---

### Workflow 3: Evidentiary Assertion Workbench
1. **Identify Gap**: A **Researcher** identifies a documented relationship (e.g. consultant hired by campaign) not yet recorded as a graph edge.
2. **Assertion Creation**:
   - Researcher selects the **Subject Entity** (e.g. consultant organization) and **Object Entity** (e.g. campaign entity).
   - Chooses a controlled **Predicate Code** (e.g. `CONSULTANT_TO`) from the vocabulary.
   - Attaches one or more **SourceLocators** specifying the document page number, visual text area, and support type.
   - Enters effective dates and explanatory notes.
3. **Promotion**:
   - If the predicate is non-sensitive, the assertion is created in `NEEDS_REVIEW` state.
   - Once a **Reviewer** confirms the evidence, the status updates to `VERIFIED`.

---

### Workflow 4: Entity De-duplication & Merging
1. **Identify Duplicates**: **Reviewers** consult the Data-Quality Center or possible duplicate lists.
2. **Compare**: Reviewer opens the Entity Comparison panel to examine shared contributions, addresses, occupation codes, and aliases.
3. **Merge Action**:
   - Reviewer clicks "Merge Entities".
   - Selects the target canonical entity and the source duplicate entity.
   - System redirects all aliases, assertions, and transactions in a single transaction.
   - Duplicate entity status updates to `MERGED`.
   - Action is logged in `AuditEvent`.
4. **Reversal**: If errors are discovered, an **Administrator** can open the audit trail and click "Reverse Merge", restoring the duplicate entity and returning its aliases.

---

### Workflow 5: Research Collections & Task Tracking
1. **Project Intake**: A **Research Manager** creates a new `ResearchCollection` (e.g. "Muelrath Public Affairs") and assigns a series of `ResearchTasks`.
2. **Gathering Evidence**: Researchers pin relevant entities, sources, contracts, and assertions to the collection directly from detail and list views.
3. **Tracking Progress**: Open questions and PRA requests are updated within the collection view until all critical details are verified.
