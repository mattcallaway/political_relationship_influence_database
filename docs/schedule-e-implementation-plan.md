# Schedule E Ingestion & Persistence Plan

This document details the implementation plan for Schedule E expenditure processing, normalizing payees, and mapping subcontractor networks.

## Ingestion Architecture

### 1. Visual Block Extraction
* Extract visual text blocks from Form 460 Schedule E pages containing payee name, address, payment code, description, and amount.
* Use geometric float coordinates to correctly align rows.

### 2. Payee Entity Normalization
* Match payee raw names against existing `Entity` records.
* Matches with confidence $\ge 95\%$ are assigned `AUTO_MATCHED` status.
* Matches with confidence $< 95\%$ remain provisional, creating `EntityMatchCandidate` records for manual review.
* Ensure newly identified payees/vendors are created as canonical `Entity` records.

### 3. Subcontractors & Agents (Schedule G Support)
* Check if expenditures are made on behalf of an agent or independent contractor (Schedule G payments).
* Store agent/contractor linkages to track subcontractor-to-primary-firm relationships.

## Database Schema Extensions
* **Expenditure Fields**:
  - `filer_committee`: ForeignKey to `Entity` (Committee).
  - `campaign`: ForeignKey to `Entity` (Campaign).
  - `payee_entity`: ForeignKey to `Entity` (Vendor / Consultant / Person).
  - `payee_raw_name`: Raw text from filing.
  - `payee_raw_address`: Raw text from filing.
  - `transaction_code`: FPPC expenditure code (e.g. CNS, TEL, PRT).
  - `description`: Text description of services.
  - `amount`: Decimal.
  - `transaction_date`: Date.
  - `agent_contractor`: ForeignKey to `Entity` (Primary vendor / contractor).
  - `is_subcontract`: Boolean flag.
  - `source_filing`: ForeignKey to `ImportBatch` or `Document`.
  - `source_page`: Integer.
