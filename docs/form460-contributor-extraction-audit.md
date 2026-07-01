# Form 460 Schedule A Contributor Extraction Audit

## 1. Analysis of Existing Extraction Failure
The existing implementation in `apps/extraction/services.py` uses a primitive regular expression to extract contributors from the text stream of a page:
```python
contrib_matches = re.findall(r'([A-Z\s,]+)\s+\$?([0-9,]+\.[0-9]{2})', text)
```
This approach fails fundamentally for several reasons:
1. **Case Sensitivity**: It looks only for uppercase names (`[A-Z\s,]+`). Most modern digital filings contain mixed-case names (e.g., "Joshua Hochberg" or "Patrick Roney"), which are completely missed.
2. **Linear Text Assumption**: It treats the page text as a continuous 1D stream. Text blocks from different columns on the same visual line or from headers/footers are intermingled, leading to false matches (e.g., associating the word "SUBTOTAL" or metadata header text with a dollar amount, as seen in the database).
3. **No Block Segmentation**: It does not group fields belonging to a single contributor block. Fields like Date, Contributor Code, Occupation, Employer, Cumulative, and Intermediary information are completely ignored.
4. **No Handling of Intermediaries or Refunds**: It cannot detect sub-sections like "Received through intermediary: ActBlue" and would either miss it or treat "ActBlue" as a separate contributor. It also ignores negative signs in refunds due to regex formatting.

---

## 2. Differences Between Born-Digital and Scanned Filings

| Attribute | Born-Digital NetFile PDFs | Scanned Historical Form 460 PDFs |
| :--- | :--- | :--- |
| **Text Layer** | Highly accurate, token-level embedded text. | None (image only) or low-quality/corrupt OCR layer. |
| **Spatial Coordinates** | Reliable character, word, and span bounding boxes. | Must be derived via layout analysis and OCR. |
| **Table Layout** | Grid lines are present but text flow may be out of order. | Often skewed, distorted, or low resolution. |
| **Address/Details** | Complete (though street addresses may be redacted). | Often heavily redacted, faded, or obscured. |
| **Extraction Approach** | 2D Geometry profile mapping using coordinates. | Image preprocessing, deskewing, row cropping, and localized OCR. |

---

## 3. Form 460 Schedule A Geometry

A standard Form 460 Schedule A page is structured in landscape orientation. When unrotated (or mapped to a normalized visual viewport of 792 x 612 pixels):

- **Header Region**: `vy` from 0 to 110. Contains statement periods, filer name, and committee ID.
- **Table Columns** (`vx` bounds):
  - **Date Received**: `vx` ~ 30 to 100.
  - **Contributor Info** (Name, Street, City, State, ZIP): `vx` ~ 100 to 380.
  - **Contributor Code** (IND, COM, OTH, PTY, SCC Checkboxes): `vx` ~ 380 to 450.
  - **Occupation / Employer**: `vx` ~ 450 to 600.
  - **Amount Received**: `vx` ~ 600 to 700.
  - **Cumulative to Date**: `vx` ~ 700 to 792.
  - **Per Election to Date**: Often overlaps with Cumulative or sits in a sub-region.
- **Footer Region**: `vy` from 470 to 612. Contains page subtotals, summary totals, and FPPC advice legends.

---

## 4. Contributor-Block Rules
A visual contributor block represents one transaction.
1. **Vertical Bounds**: A block starts at a given visual `vy` (aligned with a valid date in the date column) and ends before the next valid date or before a table separator or subtotal row.
2. **Multi-line Grouping**: All text spans falling within the block's vertical slice `[vy_start, vy_end]` must be assigned to the columns based on their horizontal `vx` coordinates.
3. **No Truncation**: Contributor names, street addresses, and employers/occupations can span multiple lines. They must be concatenated vertically in reading order rather than truncated.

---

## 5. Intermediary Rules
1. **Detection**: If the text "intermediary" or "received through" appears within the contributor info column (`vx` ~ 100 to 380) of a contributor block, it starts a subordinate section.
2. **Extraction**:
   - The text preceding this phrase belongs to the main contributor.
   - The text following this phrase belongs to the intermediary name and address.
3. **Constraint**: The intermediary must *not* be extracted as a primary contributor transaction. It must be mapped to `intermediary_name` and `intermediary_address` on the main contributor's record.

---

## 6. Refund and Negative Amount Rules
1. **Sign Preservation**: Negative contributions (refunds or adjustments) are valid. The negative sign (e.g., `-1,000.00` or `(1,000.00)`) must be preserved and parsed as a negative float.
2. **Refund Indicator**: Set `negative_or_refund = True` when the parsed amount is less than zero.
3. **No Auto-deletions**: Never discard negative rows. They are critical for transaction matching and audit trails.

---

## 7. Checkbox Strategy
1. **Digital PDFs**: Inspect drawing objects / characters (like `X`, `✔`, or custom PDF check glyphs) at the visual coordinates of each checkbox (IND, COM, OTH, PTY, SCC).
2. **Scanned PDFs**: Crop the sub-image of the checkbox column and perform a simple pixel-density / contrast analysis to detect if a box is checked, unchecked, or ambiguous.
3. **Review Routing**: If multiple checkboxes are marked, or if none are detected, classify as `unresolved` and flag for human review.

---

## 8. Evaluation Plan
To measure extraction performance, we will create a ground-truth JSON fixture representing a set of test pages. We will calculate the following metrics:
- **Block Recall**: `True Blocks Detected / Total Ground-Truth Blocks` (Target: >95%)
- **Block Precision**: `True Blocks Detected / Total Extracted Blocks` (Target: >95%)
- **Exact Name Accuracy**: `% of blocks with exact match on contributor name` (Target: >90%)
- **Amount Accuracy**: `% of blocks with exact match on transaction amount` (Target: >95%)
- **Date Accuracy**: `% of blocks with exact match on transaction date` (Target: >95%)
- **False Contributor Rate**: Number of non-contributor rows (like subtotals or headers) extracted as contributors (Target: 0).
