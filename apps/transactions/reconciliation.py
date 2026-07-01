import logging
from django.db import transaction
from apps.transactions.models import Contribution, Expenditure
from apps.extraction.services import calculate_entity_match_score

logger = logging.getLogger(__name__)

def reconcile_amendment_batches(old_batch, new_batch):
    """
    Reconciles transaction records between an original filing import batch
    and its amended counterpart. Matches corresponding records, updates status,
    and sets superseded_by references to prevent double-counting.
    """
    logger.info(f"Reconciling old batch {old_batch.id} with new amendment batch {new_batch.id}")
    
    with transaction.atomic():
        # --- 1. Reconcile Contributions ---
        old_contributions = list(Contribution.objects.filter(import_batch=old_batch))
        new_contributions = list(Contribution.objects.filter(import_batch=new_batch))
        
        matched_new_contributions = set()
        
        for old_con in old_contributions:
            best_match = None
            best_score = 0.0
            
            # Find matching new contribution
            for new_con in new_contributions:
                if new_con.id in matched_new_contributions:
                    continue
                
                # Compare attributes
                # Match score based on payee name similarity
                name_score = calculate_entity_match_score(old_con.donor_raw_name, new_con.donor_raw_name)
                amount_match = (float(old_con.amount) == float(new_con.amount))
                
                # Check date proximity (within 10 days)
                date_match = False
                if old_con.transaction_date is None and new_con.transaction_date is None:
                    date_match = True
                elif old_con.transaction_date and new_con.transaction_date:
                    date_diff_days = abs((old_con.transaction_date - new_con.transaction_date).days)
                    date_match = (date_diff_days <= 10)
                
                # Overall matching heuristic
                if amount_match and date_match and name_score >= 80.0:
                    score = name_score + (100.0 if old_con.transaction_date == new_con.transaction_date else 50.0)
                    if score > best_score:
                        best_score = score
                        best_match = new_con
            
            if best_match:
                # Link and update statuses
                old_con.superseded_by = best_match
                old_con.amendment_status = 'SUPERSEDED'
                old_con.save()
                
                best_match.amendment_status = 'AMENDED'
                best_match.save()
                
                matched_new_contributions.add(best_match.id)
                logger.info(f"Matched contribution {old_con.public_id} -> superseded by {best_match.public_id}")
            else:
                # No match found in the amended filing (record was deleted/removed)
                old_con.amendment_status = 'SUPERSEDED'
                old_con.save()
                logger.info(f"Contribution {old_con.public_id} was removed in amendment batch")

        # --- 2. Reconcile Expenditures ---
        old_expenditures = list(Expenditure.objects.filter(import_batch=old_batch))
        new_expenditures = list(Expenditure.objects.filter(import_batch=new_batch))
        
        matched_new_expenditures = set()
        
        for old_exp in old_expenditures:
            best_match = None
            best_score = 0.0
            
            # Find matching new expenditure
            for new_exp in new_expenditures:
                if new_exp.id in matched_new_expenditures:
                    continue
                
                name_score = calculate_entity_match_score(old_exp.payee_raw_name, new_exp.payee_raw_name)
                amount_match = (float(old_exp.amount) == float(new_exp.amount))
                
                date_match = False
                if old_exp.transaction_date is None and new_exp.transaction_date is None:
                    date_match = True
                elif old_exp.transaction_date and new_exp.transaction_date:
                    date_diff_days = abs((old_exp.transaction_date - new_exp.transaction_date).days)
                    date_match = (date_diff_days <= 10)
                
                if amount_match and date_match and name_score >= 80.0:
                    score = name_score + (100.0 if old_exp.transaction_date == new_exp.transaction_date else 50.0)
                    if score > best_score:
                        best_score = score
                        best_match = new_exp
            
            if best_match:
                old_exp.superseded_by = best_match
                old_exp.amendment_status = 'SUPERSEDED'
                old_exp.save()
                
                best_match.amendment_status = 'AMENDED'
                best_match.save()
                
                matched_new_expenditures.add(best_match.id)
                logger.info(f"Matched expenditure {old_exp.public_id} -> superseded by {best_match.public_id}")
            else:
                old_exp.amendment_status = 'SUPERSEDED'
                old_exp.save()
                logger.info(f"Expenditure {old_exp.public_id} was removed in amendment batch")
                
    return True
