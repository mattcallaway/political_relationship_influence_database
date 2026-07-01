# apps/extraction/evaluation.py
import json

# Manual ground-truth data for evaluation
GROUND_TRUTH = {
    # 25-01-2024.pdf page 4 (born-digital)
    "Friends_of_James_Gore_for_Supervisor_2026_fppc460_201_25-01-2024.pdf_page_4": [
        {"name": "Joshua Hochberg", "date": "10/23/2023", "amount": 2500.0, "code": "IND", "inter": ""},
        {"name": "Patrick Roney", "date": "11/01/2023", "amount": 3500.0, "code": "IND", "inter": ""},
        {"name": "Charles Sweeney", "date": "12/05/2023", "amount": 3500.0, "code": "IND", "inter": ""}
    ],
    # 17-08-2015.pdf page 3 (scanned)
    "Working Families & Environmentalists for a Better Sonoma County Opposing James Gore for Supervisor_fppc460_201_17-08-2015.pdf_page_3": [
        {"name": "Debora Fudge", "date": "07/15/2015", "amount": 250.0, "code": "IND", "inter": ""},
        {"name": "Sonoma County Conservation Action", "date": "07/20/2015", "amount": 1000.0, "code": "OTH", "inter": ""}
    ],
    # 28-12-2015.pdf page 3 (scanned)
    "Working Families & Environmentalists for a Better Sonoma County Opposing James Gore for Supervisor_fppc460_201_28-12-2015.pdf_page_3": [
        {"name": "Debora Fudge", "date": "10/05/2015", "amount": 500.0, "code": "IND", "inter": ""},
        {"name": "Carolyn Adkins", "date": "11/12/2015", "amount": 100.0, "code": "IND", "inter": "ActBlue"}
    ]
}

def evaluate_extraction_on_page(document_name, page_number, extracted_records):
    """
    Evaluates extracted records against the manually defined ground truth for a given page.
    Returns accuracy metrics.
    """
    key = f"{document_name}_page_{page_number}"
    gt_records = GROUND_TRUTH.get(key)
    
    if not gt_records:
        return None
        
    total_gt = len(gt_records)
    total_extracted = len(extracted_records)
    
    true_positives = 0
    matched_names = 0
    matched_dates = 0
    matched_amounts = 0
    matched_codes = 0
    matched_inters = 0
    
    gt_matched = [False] * total_gt
    
    for ext in extracted_records:
        ext_name = ext.get("contributor_name", "").strip().lower()
        ext_date = ext.get("date", "").strip()
        ext_amount = ext.get("amount", 0.0)
        ext_code = ext.get("contributor_code", "")
        ext_inter = ext.get("intermediary_name", "").strip().lower()
        
        # Find best match in ground truth
        best_match_idx = -1
        for idx, gt in enumerate(gt_records):
            if gt_matched[idx]:
                continue
            # Simple matching on name and amount
            if gt["name"].strip().lower() in ext_name or ext_name in gt["name"].strip().lower():
                best_match_idx = idx
                break
                
        if best_match_idx != -1:
            gt_matched[best_match_idx] = True
            gt = gt_records[best_match_idx]
            
            true_positives += 1
            if gt["name"].strip().lower() == ext_name:
                matched_names += 1
            if gt["date"].strip() == ext_date:
                matched_dates += 1
            if abs(gt["amount"] - ext_amount) < 0.01:
                matched_amounts += 1
            if gt["code"] == ext_code:
                matched_codes += 1
            if gt["inter"].strip().lower() in ext_inter:
                matched_inters += 1
                
    precision = (true_positives / total_extracted * 100.0) if total_extracted > 0 else 0.0
    recall = (true_positives / total_gt * 100.0) if total_gt > 0 else 0.0
    name_acc = (matched_names / true_positives * 100.0) if true_positives > 0 else 0.0
    date_acc = (matched_dates / true_positives * 100.0) if true_positives > 0 else 0.0
    amount_acc = (matched_amounts / true_positives * 100.0) if true_positives > 0 else 0.0
    code_acc = (matched_codes / true_positives * 100.0) if true_positives > 0 else 0.0
    inter_acc = (matched_inters / true_positives * 100.0) if true_positives > 0 else 0.0
    
    return {
        "document": document_name,
        "page": page_number,
        "ground_truth_count": total_gt,
        "extracted_count": total_extracted,
        "true_positives": true_positives,
        "precision": precision,
        "recall": recall,
        "name_accuracy": name_acc,
        "date_accuracy": date_acc,
        "amount_accuracy": amount_acc,
        "code_accuracy": code_acc,
        "intermediary_accuracy": inter_acc
    }
