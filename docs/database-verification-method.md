# Database Verification Methodology

This document details the validation routines used to verify the integrity and completeness of data imported into the Sonoma County Political Relationship & Influence Database.

---

## 1. Import Completeness Verification

To verify that the consolidated Excel workbook (v5) is completely and accurately present:
1. **Source Records Verification**: Check that all documents and sources referenced in the workbook map to entries in the `Source` and `Document` registries.
2. **Entity Linkage Integrity**: Ensure every canonical entity maps back to its primary import row using `LegacyIdentifier` mapping.
3. **Transaction Totals Validation**: Reconcile aggregated campaign contributions against the transaction totals reported in original Form 460 filings.

---

## 2. Dynamic Integrity Checks

The system performs read-only checks to identify quality issues:
* **Orphan Source Detection**: Identifies assertions or transaction profiles lacking a direct parent link to a `Source` or `SourceLocator`.
* **Duplicate Committee IDs**: Matches state FPPC ID fields against existing records to catch duplicate committee registrations.
* **Provisional Aging Threshold**: Flags machine-extracted entities that have remained in the `PROVISIONAL_AUTO_CREATED` state for over 30 days without review.
