# apps/extraction/validation.py
import datetime

def validate_contribution_record(record, statement_start=None, statement_end=None, subtotal_value=None, other_records=None):
    """
    Validates an extracted contribution record against FPPC Form 460 Schedule A schema and visual rules.
    Returns:
        - confidence_rating: 'HIGH', 'MEDIUM', 'LOW'
        - field_confidences: dict of field -> float score (0-100)
        - warnings: list of string warnings
    """
    warnings = []
    field_confidences = {
        "date": 100.0,
        "name": 100.0,
        "amount": 100.0,
        "code": 100.0,
        "occupation": 100.0,
        "employer": 100.0,
        "intermediary": 100.0
    }
    
    # 1. Validate Date
    date_val = record.get("date")
    parsed_date = None
    if not date_val:
        field_confidences["date"] = 0.0
        warnings.append("missing_date")
    else:
        try:
            # Parse date in formats like MM/DD/YYYY or MM/DD/YY
            parts = date_val.split("/")
            if len(parts) == 3:
                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                if year < 100:
                    year += 2000
                parsed_date = datetime.date(year, month, day)
                
                # Check relation to statement period
                if statement_start and parsed_date < statement_start:
                    warnings.append("date_before_statement_period")
                    field_confidences["date"] = 60.0
                if statement_end and parsed_date > statement_end:
                    warnings.append("date_after_statement_period")
                    field_confidences["date"] = 60.0
            else:
                raise ValueError()
        except Exception:
            field_confidences["date"] = 30.0
            warnings.append("invalid_date_format")

    # 2. Validate Name
    name_val = record.get("contributor_name")
    if not name_val or len(name_val.strip()) < 3:
        field_confidences["name"] = 0.0
        warnings.append("missing_contributor_name")
    else:
        # Check for possible truncation or noise
        if name_val.strip().endswith(",") or name_val.strip().endswith("&"):
            warnings.append("contributor_name_possibly_truncated")
            field_confidences["name"] = 50.0

    # 3. Validate Amount
    amount_val = record.get("amount")
    parsed_amount = 0.0
    if amount_val is None:
        field_confidences["amount"] = 0.0
        warnings.append("missing_amount")
    else:
        try:
            # Keep negative sign intact
            parsed_amount = float(str(amount_val).replace(",", "").replace("$", ""))
            if parsed_amount == 0.0:
                warnings.append("zero_amount")
        except ValueError:
            field_confidences["amount"] = 20.0
            warnings.append("invalid_amount_format")

    # 4. Checkbox Code Consistency
    code_val = record.get("contributor_code")
    code_conf = record.get("contributor_code_confidence", 100.0)
    field_confidences["code"] = code_conf
    
    if not code_val or code_val == "unresolved":
        warnings.append("missing_contributor_code")
        field_confidences["code"] = 0.0
    else:
        # Cross-field logic check: IND should have occupation/employer, others should be blank
        is_ind = code_val == "IND"
        has_occ_emp = bool(record.get("occupation")) or bool(record.get("employer"))
        if is_ind and not has_occ_emp and parsed_amount >= 100.0:
            warnings.append("individual_missing_occupation_employer")
            field_confidences["occupation"] = 50.0
            field_confidences["employer"] = 50.0
        elif not is_ind and has_occ_emp:
            warnings.append("non_individual_has_occupation_employer")
            
    # 5. Intermediary Containment Check
    inter_name = record.get("intermediary_name")
    if inter_name:
        if inter_name.strip().upper() == "ACTBLUE" and record.get("contributor_name").strip().upper() == "ACTBLUE":
            warnings.append("intermediary_extracted_as_contributor")
            field_confidences["intermediary"] = 40.0

    # 6. Duplication Check within page
    if other_records:
        for other in other_records:
            if other != record:
                if (other.get("date") == record.get("date") and 
                    other.get("contributor_name") == record.get("contributor_name") and 
                    other.get("amount") == record.get("amount")):
                    warnings.append("duplicate_transaction_on_page")
                    
    # Calculate Overall Block-level Confidence Rating
    min_confidence = min(field_confidences.values())
    if min_confidence >= 85.0 and len(warnings) == 0:
        rating = "HIGH"
    elif min_confidence >= 50.0 and len(warnings) <= 2:
        rating = "MEDIUM"
    else:
        rating = "LOW"
        
    return rating, field_confidences, warnings
