# V5 Import Field Map

This document outlines how fields from the Excel workbook `Sonoma_Political_Influence_Database_v5_consolidated.xlsx` map to the expanded Sonoma County Political Influence Database Django models.

---

## 1. Sheet: Sources
* **SourceID** $\rightarrow$ `Source.public_id`
* **Title** $\rightarrow$ `Source.title`
* **SourceType** $\rightarrow$ `Source.source_type`
* **IssuingBodyPublisher** $\rightarrow$ `Source.issuing_body`
* **Author** $\rightarrow$ `Source.author`
* **PublicationDate** $\rightarrow$ `Source.publication_date`
* **AccessDate** $\rightarrow$ `Source.access_date`
* **URL** $\rightarrow$ `Source.original_url`
* **ArchiveURL** $\rightarrow$ `Source.archive_url`
* **Jurisdiction** $\rightarrow$ `Source.jurisdiction`
* **ReliabilityTier** $\rightarrow$ `Source.reliability`
* **Notes** $\rightarrow$ `Source.notes`

---

## 2. Sheet: Entity_Index
* **EntityID** $\rightarrow$ `Entity.public_id`
* **EntityType** $\rightarrow$ `Entity.entity_type`
* **CanonicalName** $\rightarrow$ `Entity.canonical_name`
* **Status** $\rightarrow$ `Entity.status` (Mapped to `'VERIFIED'`, `'NEEDS_REVIEW'`, etc.)
* **Jurisdiction** $\rightarrow$ `Entity.jurisdiction`
* **Notes** $\rightarrow$ `Entity.notes`

---

## 3. Sheet: People
* **PersonID** $\rightarrow$ `Person.entity` (Linked to `Entity.public_id`)
* **FullName** $\rightarrow$ `Person.display_name`
* **FirstName** $\rightarrow$ `Person.first_name`
* **MiddleName** $\rightarrow$ `Person.middle_name`
* **LastName** $\rightarrow$ `Person.last_name`
* **Suffix** $\rightarrow$ `Person.suffix`
* **PrimaryRole** $\rightarrow$ `Person.public_role` & `Person.occupation`
* **Biography** $\rightarrow$ `Person.notes`

---

## 4. Sheet: Organizations
* **OrgID** $\rightarrow$ `Organization.entity` (Linked to `Entity.public_id`)
* **CanonicalName** $\rightarrow$ `Organization.legal_name`
* **OrgType** $\rightarrow$ `Organization.org_category`
* **Description** $\rightarrow$ `Organization.notes`

---

## 5. Sheet: Aliases
* **EntityID** $\rightarrow$ `Alias.entity` (Linked to `Entity.public_id`)
* **Alias** $\rightarrow$ `Alias.alias_text`
* **AliasType** $\rightarrow$ `Alias.alias_type`
* **SourceID** $\rightarrow$ `Alias.source_locator` (Created and linked)

---

## 6. Sheet: Campaigns
* **CampaignID** $\rightarrow$ `Campaign.entity` (Linked to `Entity.public_id`)
* **CampaignName** $\rightarrow$ `Campaign.campaign_name`
* **CandidatePersonID** $\rightarrow$ `Campaign.candidate` (Linked to `Entity.public_id`)
* **CommitteeID** $\rightarrow$ `Campaign.committee` (Linked to `Entity.public_id`)
* **OfficeID** $\rightarrow$ `Campaign.office` (Linked to `Entity.public_id`)
* **Outcome** $\rightarrow$ `Campaign.outcome`

---

## 7. Sheet: Committees
* **CommitteeID** $\rightarrow$ `Committee.entity` (Linked to `Entity.public_id`)
* **CommitteeName** $\rightarrow$ `Committee.committee_name`
* **CommitteeType** $\rightarrow$ `Committee.committee_type`
* **FPPCID** $\rightarrow$ `Committee.fppc_id`
* **PrincipalOfficerID** $\rightarrow$ `Committee.controlling_candidate` (Linked to `Entity.public_id`)

---

## 8. Sheet: Projects
* **ProjectID** $\rightarrow$ `Project.entity` (Linked to `Entity.public_id`)
* **ProjectName** $\rightarrow$ `Project.entity.canonical_name`
* **ProjectType** $\rightarrow$ `Project.project_category`
* **Jurisdiction** $\rightarrow$ `Project.jurisdiction`
* **Location** $\rightarrow$ `Project.location`
* **ApplicantEntityID** $\rightarrow$ `Project.applicant` (Linked to `Entity.public_id`)
* **OwnerEntityID** $\rightarrow$ `Project.property_owner` (Linked to `Entity.public_id`)
* **Status** $\rightarrow$ `Project.status`

---

## 9. Sheet: Assertions
* **AssertionID** $\rightarrow$ `Assertion.public_id`
* **SubjectEntityID** $\rightarrow$ `Assertion.subject_entity` (Linked to `Entity.public_id`)
* **PredicateCode** $\rightarrow$ `Assertion.predicate`
* **ObjectEntityID** $\rightarrow$ `Assertion.object_entity` (Linked to `Entity.public_id`)
* **ObjectValue** $\rightarrow$ `Assertion.object_value`
* **ClaimType** $\rightarrow$ `Assertion.claim_type`
* **StartDate** $\rightarrow$ `Assertion.effective_start`
* **EndDate** $\rightarrow$ `Assertion.effective_end`
* **VerificationStatus** $\rightarrow$ `Assertion.verification_status`
* **Notes** $\rightarrow$ `Assertion.explanatory_note`

---

## 10. Sheet: Assertion_Sources
* **AssertionID** $\rightarrow$ `AssertionSource.assertion`
* **SourceID** $\rightarrow$ `AssertionSource.source`
* **SupportType** $\rightarrow$ `AssertionSource.support_type`
* **PageSection** $\rightarrow$ `AssertionSource.source_locator.section`
* **EvidenceSummary** $\rightarrow$ `AssertionSource.evidence_note`
