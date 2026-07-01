# Anti-Drift Principles & Development Rules

To prevent technical and product drift, the development of the Sonoma County Political Relationship & Influence Database must adhere to these 10 non-negotiable rules.

---

## The 10 Anti-Drift Rules

### 1. No Parser-Only Milestones
No milestone or phase of development may consist entirely of OCR, parser, or backend ingestion work. Every release must deliver visible improvements to researcher usability, data connection, or evidence review.

### 2. Mandatory Usability Upgrades
Every database expansion or model modification must be accompanied by updates to the UI, ensuring researchers can view, verify, and edit the new records.

### 3. Parser End-to-End Delivery
No ingestion adapter or parser is complete until its records appear fully integrated in:
* Unified central search
* Entity profiles
* Research collections
* Chronological timelines
* Review queues
* Graph and CSV exports
* Automated data-quality checks

### 4. Direct Provenance for Edges
No relationship edge may exist in any graph export or visual network map without a structured originating database record (e.g. Contribution, Appointment, Vote) and a verified `SourceLocator` mapping back to page-level document evidence.

### 5. Non-Judgmental Predicates
No relationship, link, or assertion may be automatically labeled using pejorative terms such as *influence, control, coordination, corruption, wrongdoing,* or *conflict of interest*. The platform records evidence of connections; normative interpretations belong strictly to the researcher.

### 6. No Silent Machine Verifications
No machine match or automated deduplication suggestion may silently become human-verified. Automatic matching at high confidence thresholds produces `AUTO_MATCHED` or `PROVISIONAL` links, which must remain clearly flagged and reviewable in the UI.

### 7. Immutable Raw Extractions
No record correction or merge operation may overwrite raw machine-extracted data or delete prior reviewer history. Correction histories and original raw states must be preserved for audit and rollback capabilities.

### 8. Entity Subtype Consolidations
No new entity models or tables may be created when an existing canonical `Entity` type or subtype (e.g. `PERSON`, `ORGANIZATION`, `COMMITTEE`, `COMPANY`) can represent the concept. Shared attributes must reside in the central table.

### 9. Hard Deletion Prohibitions
No source-backed transactional record, document, or assertion may be hard deleted through normal research tools. If a record is incorrect, it must be marked as `REJECTED`, `SUPERSEDED`, or `WITHHELD` to preserve the audit trail.

### 10. Objective Metrics Only
No dashboard metric, card, or connection index should imply normative judgment. Count and volume indicators must reflect purely descriptive quantitative figures (e.g., transaction volume, contract value, meeting attendance) rather than qualitative influence rankings.
