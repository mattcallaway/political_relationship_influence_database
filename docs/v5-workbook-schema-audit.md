# Workbook Migration Report & Schema Audit (v5 Consolidated)
**Application**: Sonoma Political Relationship and Influence Database  
**Primary Seed File**: `data/imports/Sonoma_Political_Influence_Database_v5_consolidated.xlsx` (Ingested from `D:\Downloads\Sonoma County Political Influence Database.xlsx`)  
**Audit Date**: June 2026  

---

## 1. Executive Summary
This document provides an audit of the authentic seed dataset `Sonoma County Political Influence Database.xlsx` (243 KB, 29 sheets) for the Sonoma Political Relationship and Influence Database. The workbook consolidates years of civic research in Sonoma County, California—spanning public officials, political consultants, land developers, campaign committees, FPPC Form 460 contributions and expenditures, public record requests (PRA), assertions, and research workflows.

The migration strategy ensures **zero silent data loss**, complete **provenance preservation**, and an auditable mapping from legacy spreadsheet identifiers (`P000001`, `ORG000001`, `SRC000001`, `AST000001`, `CON000001`, `EXP000001`, `LEG...`) to the normalized PostgreSQL multi-app Django schema.

---

## 2. Complete Inventory of Workbook Sheets (29 Total)

| Sheet Name | Purpose & Description | Migration Target Model | Key Columns / Identifier |
| :--- | :--- | :--- | :--- |
| **`Dashboard`** | High-level research summary metrics and entity highlights | Analytical view / UI Dashboard | N/A |
| **`Entity_Index`** | Canonical master directory of all entities | `apps.entities.models.Entity` | `EntityID`, `CanonicalName`, `EntityType` |
| **`People`** | Physical individuals (officials, consultants, donors) | `apps.entities.models.Person` | `PersonID` (1:1 with `EntityID`), `FullName` |
| **`Organizations`** | Corporations, PACs, lobbying firms, public bodies | `apps.entities.models.Organization` | `OrganizationID`, `LegalName`, `CommitteeID` |
| **`Aliases`** | Alternate names, DBAs, and former committee names | `apps.entities.models.Alias` | `AliasID`, `EntityID`, `AliasText` |
| **`Campaigns`** | Candidate and ballot measure campaign cycles | `apps.campaigns.models.Campaign` | `CampaignID`, `CampaignName`, `Year` |
| **`Committees`** | FPPC candidate/PAC committees | `apps.campaigns.models.Committee` | `CommitteeID`, `FPPC_ID`, `CommitteeName` |
| **`Projects`** | Land development, zoning, and municipal projects | `apps.projects.models.Project` | `ProjectID`, `ProjectName`, `Jurisdiction` |
| **`Public_Offices`** | Elected and appointed public seats | `apps.government.models.PublicOffice` | `OfficeID`, `OfficeName`, `Jurisdiction` |
| **`Government_Bodies`** | County boards, city councils, commissions | `apps.government.models.GovernmentBody` | `BodyID`, `BodyName`, `Jurisdiction` |
| **`Sources`** | Form 460 disclosures, minutes, news, PRAs | `apps.sources.models.Source` & `Document` | `SourceID`, `Title`, `SourceType`, `URL` |
| **`Assertions`** | Factual claims, roles, and connections | `apps.assertions.models.Assertion` | `AssertionID`, `SubjectEntityID`, `PredicateCode` |
| **`Assertion_Sources`**| Specific page and locator evidence citations | `apps.assertions.models.AssertionSource` | `AssertionID`, `SourceID`, `DocumentPage` |
| **`Contributions`** | Form 460 Schedule A campaign contributions | `apps.transactions.models.Contribution` | `ContributionID`, `FilerCommitteeID`, `Amount` |
| **`Expenditures`** | Form 460 Schedule E campaign expenditures | `apps.transactions.models.Expenditure` | `ExpenditureID`, `FilerCommitteeID`, `Amount` |
| **`Appointments`** | Public board and commission appointments | `apps.government.models.Appointment` | `AppointmentID`, `PersonID`, `BodyID` |
| **`Contracts`** | Public agency contracts and consulting agreements | `apps.transactions.models.Contract` | `ContractID`, `AgencyID`, `VendorID` |
| **`Events`** | Public meetings, forums, fundraisers | `apps.government.models.Event` | `EventID`, `EventName`, `EventDate` |
| **`Research_Queue`** | Open investigative leads and tasks | `apps.research.models.ResearchTask` | `TaskID`, `TaskTitle`, `Status` |
| **`Entity_Match_Queue`**| Potential fuzzy duplicate entity matches | `apps.research.models.EntityMatchCandidate` | `CandidateID`, `EntityID1`, `EntityID2` |
| **`PRA_Requests`** | Public Records Act request tracking | `apps.research.models.PRARequest` | `PRA_ID`, `AgencyID`, `RequestSummary` |
| **`Change_Log`** | Auditable log of workbook revisions | `apps.audit.models.ChangeLog` | `ChangeID`, `Timestamp`, `TableName` |
| **`Reference_Data`** | Controlled vocabularies and taxonomies | `apps.audit.models.ControlledVocabularyValue`| `ListName`, `Code`, `Label` |
| **`Predicate_Vocabulary`**| Controlled relationship codes & inverse rules | `apps.audit.models.ControlledVocabularyValue`| `PredicateCode`, `Label`, `Category` |
| **`Inbox_Intake`** | Staging area for raw submitted documents | `apps.research.models.IntakeItem` | `IntakeID`, `URLorFile`, `ItemType` |
| **`Import_Templates`**| Required/recommended field mapping templates | Reference guide / Management Command | `TemplateName`, `RequiredFields` |
| **`Methodology`** | Research standards and evidentiary rules | System documentation | Principle, Standard |
| **`Legacy_ID_Map`** | Crosswalk mapping from v3/v4 to current IDs | `apps.audit.models.LegacyIdentifier` | `LegacyID`, `CurrentID`, `MigrationNotes` |
| **`Research_Locations`**| Repositories, agency clerks, and filing portals | `apps.research.models.ResearchLocation` | `LocationID`, `Repository`, `Jurisdiction` |

---

## 3. Controlled Vocabularies & Taxonomies Seeded from Workbook

1. **Entity Types** (`Reference_Data`): `PERSON`, `ORGANIZATION`, `CAMPAIGN`, `PROJECT`, `COMMITTEE`, `GOVERNMENT_BODY`
2. **Predicates** (`Predicate_Vocabulary`): `principal_of`, `employee_of`, `consultant_to`, `contributed_to`, `voted_for`, `represented_client`, `appointed_to`, `candidate_for`, `associated_with`, `possible_involvement_in`, `worked_to_pass`
3. **Source Types**: `FORM_460`, `MEETING_MINUTES`, `STAFF_REPORT`, `LOBBYING_DISCLOSURE`, `CONTRACT`, `PRA_RESPONSE`, `NEWS_ARTICLE`
4. **Claim Types**: `FACTUAL`, `INTERPRETIVE`, `ALLEGATION`, `HYPOTHESIS`, `CONTEXT`

---

## 4. Migration Strategy & Repeatable Management Command
The management command `python manage.py import_v5_workbook` will:
1. Wrap all imports in database transactions per sheet.
2. Maintain idempotency by checking `LegacyIdentifier` and public IDs (`P000001`, `ORG000001`, etc.).
3. Store raw unparsed strings in `ImportRow` staging for any non-conforming rows.
4. Report detailed row-level summary counts and log warnings without discarding data.
