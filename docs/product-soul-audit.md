# Product Soul Audit: Correcting Product Drift

This audit examines the current state of the Sonoma County Political Relationship & Influence Database, identifies technical and conceptual product drift, and outlines structural corrections to align the software with its civic-research charter.

---

## 1. Audit Dimensions & Findings

### Campaign-Finance Centricity vs. Cross-Domain Relationships
* **Current State**: The system is highly optimized for Form 460 Schedule A campaign contributions.
* **Drift**: Concepts like "review queue" and "provisional entities" were initially implemented around transaction imports. Other schemas like appointments, votes, contracts, and lobbying lack equivalent UI visibility and editing controls.
* **Correction**: Standardize all models under the central Entity, Document, and Assertion frameworks, ensuring campaign finance is treated as one adapter among many.

### OCR & Parser Driving Product Architecture
* **Current State**: Visual parsing and OCR processing models are highly complex, consuming significant developer attention.
* **Drift**: Parser success was temporarily treated as milestone completion.
* **Correction**: Re-anchor parsers as input pipelines. A parser is not complete until its records are queryable in the global search index, displayed on profile workspaces, incorporated in timelines, and included in network exports.

### Central Entity System Usage
* **Current State**: The Entity model serves as the common denominator.
* **Drift**: Some sub-records (e.g. raw donor names) existed as plain strings before being linked.
* **Correction**: Every ingestion adapter must immediately write to the Entity and Alias tables (categorized as provisional if not matched), ensuring there are no unmapped raw-string actors in the system.

### Entity Profile Coverage
* **Current State**: Entity profiles feature tabs for contributions, timeline, and assertions.
* **Drift**: Crucial relational categories (lobbying activities, appointments, board memberships, motions moved/seconded, votes cast, active research tasks, open questions) are not fully integrated into a unified profile view.
* **Correction**: Expand `entity_detail.html` into a complete research dashboard showing all cross-domain relationships, data-quality issues, duplicate alerts, and active task checkers.

### Relationship Provenance & Assertions
* **Current State**: Graph projections and assertions exist.
* **Drift**: There is a risk of generating graph edges without explicit source locator attachments or matching verification metadata.
* **Correction**: Enforce that every relationship edge must link to a structured database record (e.g., a Contribution, an Appointment, a LobbyingActivity) which in turn links to a `SourceLocator`.

### Provisional vs. Verified Distinction
* **Current State**: Provisional status (`PROVISIONAL_AUTO_CREATED`) exists.
* **Drift**: The visual interface does not always highlight the distinction between provisional records and human-verified files.
* **Correction**: Apply distinctive visual treatments (badges, warnings, color schemes) to ensure provisional data is flagged as unverified research leads.

### Research Collection Investigation Workspace
* **Current State**: Research collections exist as basic lists.
* **Drift**: It functions as a collection bookmark folder rather than an active workspace.
* **Correction**: Overhaul `ResearchCollection` to act as an investigative command center for complex networks like "Muelrath Public Affairs", showing all entities, tasks, questions, timeline events, and data gaps.

### UI Modification Capabilities
* **Current State**: Core modifications are done via side-by-side matches.
* **Drift**: Researchers cannot easily create connections, write custom assertions, or correct OCR text directly within the document viewer UI.
* **Correction**: Introduce forms to add assertions, log new source files, and execute inline edits across all profile domains.

### Research Gaps & Open Questions
* **Current State**: The database tracks completed records.
* **Drift**: Missing documents, public record requests (PRAs), and unanswered research questions are not tracked.
* **Correction**: Implement structured models for `ResearchTask` and `OpenQuestion` connected to entities, collections, and sources.

---

## 2. Soul Audit Scorecard

| Evaluation Question | Audit Status | Required Action |
| :--- | :--- | :--- |
| Is the app too campaign-finance-centric? | Yes | Add Schedule E, appointments, lobbying, and contracts to main workspaces. |
| Is OCR driving the product? | Yes | Shift focus to researcher-facing verification and profile workspaces. |
| Do all records use the central Entity system? | Partially | Ensure all raw parsed entities are cataloged as provisional profiles immediately. |
| Do entity profiles show the full picture? | No | Expand profile templates to show lobbying, boards, votes, tasks, and data errors. |
| Are all relationships source-backed? | Yes | Maintain strict ForeignKey validation to `SourceLocator`. |
| Are provisional/verified states distinguished? | Partially | Add visual treatments to distinguish provisional profiles and matches. |
| Is the collection a true workspace? | No | Redesign collection template with task trackers and empty research-gap blocks. |
| Do graph exports contain provenance? | Partially | Include record public IDs, source counts, and statuses in GraphML exports. |
| Can sources be inspected easily? | Partially | Link every table row directly to its source document page locator. |
| Can users manipulate central records via UI? | Partially | Add editing views for all transactional record types. |
| Does the system support tasks & source gaps? | No | Create models and forms for research tasks and questions. |
| Is technical complexity serving research? | No | Simplify backend parsers; focus on dashboard usability and data connectivity. |
