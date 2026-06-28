# Workbook Migration Report & Schema Audit (v5)
**Application**: Sonoma Political Relationship and Influence Database  
**Seed File**: `data/imports/Sonoma_Political_Influence_Database_v5_consolidated.xlsx`  
**Audit Date**: June 2026  

---

## 1. Executive Summary
This document provides a comprehensive audit of the seed dataset `Sonoma_Political_Influence_Database_v5_consolidated.xlsx` for the Sonoma Political Relationship and Influence Database. The seed workbook consolidates documented public records, entities, campaign disclosures, assertions, and research workflows in Sonoma County, California.

The migration strategy ensures **zero silent data loss**, complete **provenance preservation**, and an auditable mapping from legacy spreadsheet identifiers to the normalized PostgreSQL multi-app Django schema.

---

## 2. Inventory of Workbook Sheets & Column Structures

### 2.1 `Controlled_Vocabularies`
* **Purpose**: Defines standardized codes and taxonomies for entity classification, relationship types, claim categories, and source reliability.
* **Columns (5)**: `Vocabulary_Category`, `Code`, `Label`, `Description`, `Is_Active`
* **Total Records**: 16
* **Migration Target**: `apps.audit.models.ControlledVocabularyValue`

### 2.2 `Entities`
* **Purpose**: Base table for all physical individuals and corporate/public organizations.
* **Columns (5)**: `Legacy_ID`, `Canonical_Name`, `Entity_Type`, `Status`, `Notes`
* **Total Records**: 6
* **Migration Target**: `apps.entities.models.Entity` (base model with UUID primary key and readable `public_id`).

### 2.3 `Persons`
* **Purpose**: Specific details for physical human beings in the public domain.
* **Columns (7)**: `Legacy_ID`, `Full_Name`, `First_Name`, `Last_Name`, `Occupation`, `Public_Role`, `Jurisdiction`
* **Total Records**: 2
* **Migration Target**: `apps.entities.models.Person` (1-to-1 extension of `Entity`).

### 2.4 `Organizations`
* **Purpose**: Legal entities, committees, developer corporations, government agencies, and lobbying firms.
* **Columns (6)**: `Legacy_ID`, `Legal_Name`, `Common_Name`, `Org_Category`, `Committee_ID`, `Jurisdiction`
* **Total Records**: 4
* **Migration Target**: `apps.entities.models.Organization` (1-to-1 extension of `Entity`).

### 2.5 `Sources`
* **Purpose**: Primary evidentiary documents and filings supporting all factual claims.
* **Columns (7)**: `Legacy_Source_ID`, `Title`, `Source_Type`, `Publisher`, `Filing_Date`, `URL`, `Reliability`
* **Total Records**: 2
* **Migration Target**: `apps.sources.models.Source` and `apps.documents.models.Document`.

### 2.6 `Assertions`
* **Purpose**: Documented factual claims, relationships, and roles connecting entities.
* **Columns (9)**: `Legacy_Assertion_ID`, `Subject_Legacy_ID`, `Predicate`, `Object_Legacy_ID`, `Literal_Value`, `Claim_Type`, `Confidence`, `Source_Legacy_ID`, `Source_Page`
* **Total Records**: 2
* **Migration Target**: `apps.assertions.models.Assertion` & `apps.assertions.models.AssertionSource`.

### 2.7 `Contributions`
* **Purpose**: Campaign contributions extracted from Form 460 Schedule A filings.
* **Columns (10)**: `Legacy_Trans_ID`, `Filer_Committee_ID`, `Donor_Legacy_ID`, `Donor_Raw_Name`, `Transaction_Date`, `Amount`, `Schedule`, `Source_Legacy_ID`, `Source_Page`, `Review_Status`
* **Total Records**: 1
* **Migration Target**: `apps.transactions.models.Contribution`.

### 2.8 `Expenditures`
* **Purpose**: Campaign expenditures extracted from Form 460 Schedule E filings.
* **Columns (11)**: `Legacy_Trans_ID`, `Filer_Committee_ID`, `Payee_Legacy_ID`, `Payee_Raw_Name`, `Transaction_Date`, `Amount`, `Description`, `Schedule`, `Source_Legacy_ID`, `Source_Page`, `Review_Status`
* **Total Records**: 1
* **Migration Target**: `apps.transactions.models.Expenditure`.

### 2.9 `Research_Workflow`
* **Purpose**: Research tracking tasks, pending verifications, and investigation logs.
* **Columns (6)**: `Legacy_Task_ID`, `Task_Title`, `Assigned_Researcher`, `Priority`, `Status`, `Notes`
* **Total Records**: 1
* **Migration Target**: `apps.research.models.ResearchTask`.

### 2.10 `Legacy_ID_Mappings`
* **Purpose**: Cross-walk mapping table connecting legacy workbook IDs to system target models.
* **Columns (4)**: `Legacy_ID`, `Source_Sheet`, `Target_Model`, `System_Public_ID_Prefix`
* **Total Records**: 12
* **Migration Target**: `apps.audit.models.LegacyIdentifier`.

---

## 3. Controlled Vocabularies & Taxonomies Seeded

1. **Entity Types**: `PERSON`, `ORGANIZATION`
2. **Organization Categories**: `CAMPAIGN_COMMITTEE`, `DEVELOPER_CORP`, `GOVT_AGENCY`, `LOBBYING_FIRM`
3. **Source Types**: `FORM_460`, `MEETING_MINUTES`, `STAFF_REPORT`
4. **Claim Types**: `FACTUAL`, `INTERPRETIVE`, `ALLEGATION`, `HYPOTHESIS`
5. **Predicates**: `CONTRIBUTED_TO`, `EMPLOYED_BY`, `REPRESENTED_CLIENT`, `VOTED_FOR`
6. **Review Statuses**: `PROPOSED`, `APPROVED`, `CORRECTED`, `REJECTED`

---

## 4. Migration Strategy & ID Resolution Rules
- **Idempotency**: Implemented via `python manage.py import_v5_workbook --dry-run`.
- **Public ID Assignment**: Internal UUIDs are primary keys. Public human-readable IDs (`P000001`, `ORG000001`, `SRC000001`, `AST000001`, `CON000001`, `EXP000001`) are assigned upon approval.
- **Ambiguity Handling**: Raw strings (e.g., `Donor_Raw_Name`) are preserved in extraction staging models. Unmatched entities require manual reviewer approval before canonical entity resolution.
