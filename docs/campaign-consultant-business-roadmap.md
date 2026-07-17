# Campaign-Consultant-Business Roadmap

This roadmap redirects development priorities away from government meetings and agendas, focusing exclusively on building out relationship tracking among campaigns, consultants, vendors, donors, and businesses.

## Refocused Roadmap Phases

### Phase 1: Campaign–Consultant–Business Relationship Core (Current Milestone)
* **Goal**: Build complete campaign, consultant/firm, business, and individual profile hubs linked by Schedule E expenditure records and campaign-role mappings.
* **Deliverables**:
  1. Schedule E visual payee extraction persisted to `Expenditure` model.
  2. Normalize campaign vendors and consultants as canonical entities.
  3. Support subcontractor and agent payments tracking.
  4. Develop Refocused Profile Hubs (Campaign, Consultant/Firm, Business/Industry, Individual, Committee).
  5. Add Shared-Consultant, Shared-Vendor, and Shared-Donor analyzers showing raw underlying transaction records.
  6. Refocus search/filters around campaigns, consultants, donors, and cycles.

### Phase 2: Form 410, 461, 496, and 497 Ingestion
* **Goal**: Expand financial connections with independent expenditures, late contributions, and committee organization structures.
* **Deliverables**:
  1. Parse Form 410 (Statement of Organization) to map treasurers, sponsors, and controlled candidates.
  2. Ingest Form 496 (Late Independent Expenditure Reports) and Form 497 (Late Contribution Reports).
  3. Map independent expenditure targeting (SUPPORTED vs. OPPOSED campaigns).

### Phase 3: Lobbying & Client registries
* **Goal**: Link campaign contributions and consulting firms to private-sector client representations.
* **Deliverables**:
  1. Ingest quarterly lobbying disclosures mapping firms to clients, targets, and compensation.
  2. Correlate consultant client lists with campaign payments.

### Phase 4: Campaign Infrastructure Analysis
* **Goal**: Uncover recurring networks of vendors, treasurers, and consultants serving multiple candidates.
* **Deliverables**:
  1. Build multi-candidate shared infrastructure comparison dashboard.
  2. Generate dynamic Cytoscape network projection diagrams filtered by campaign, donor, or consultant.
