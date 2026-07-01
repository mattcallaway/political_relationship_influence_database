# apps/extraction/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from apps.documents.models import Document
from apps.entities.models import Entity, Alias, EntityStatus, EntityMerge
from apps.transactions.models import Contribution, ReviewStatus, AuditEvent
from apps.extraction.models import EntityMatchAttempt

def review_side_by_side(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    # Fetch contributions directly from central DB
    contributions = Contribution.objects.filter(document=document).order_by('document_page__page_number', 'public_id')
    
    # Expose list of canonical entities for rematch/merge selection UI
    entities = Entity.objects.exclude(status=EntityStatus.MERGED).order_by('canonical_name')
    
    return render(request, 'extraction/side_by_side.html', {
        'document': document,
        'contributions': contributions,
        'entities': entities
    })

@require_POST
def confirm_match(request, contribution_id):
    con = get_object_or_404(Contribution, id=contribution_id)
    
    with transaction.atomic():
        con.review_status = ReviewStatus.VERIFIED
        con.save()
        
        # Log match attempt confirmation
        if con.match_attempt:
            con.match_attempt.match_method = "REVIEWER_CONFIRMED"
            con.match_attempt.save()
            
        # Update entity status to verified/reviewed
        if con.donor_entity:
            if con.donor_entity.status == EntityStatus.PROVISIONAL_AUTO_CREATED:
                con.donor_entity.status = EntityStatus.VERIFIED
                con.donor_entity.save()
                
        # Record Audit Event
        AuditEvent.objects.create(
            action="MATCH_CONFIRMED",
            table_name="Contribution",
            record_id=str(con.id),
            prior_value={"review_status": "AUTO_IMPORTED"},
            new_value={"review_status": "VERIFIED"},
            user=request.user if request.user.is_authenticated else None,
            reason="Reviewer confirmed automated match."
        )
        
    return redirect('review_side_by_side', document_id=con.document.id)

@require_POST
def rematch_contribution(request, contribution_id):
    con = get_object_or_404(Contribution, id=contribution_id)
    target_entity_id = request.POST.get('target_entity')
    reason = request.POST.get('reason', '')
    
    if not target_entity_id:
        return HttpResponseBadRequest("Missing target_entity ID")
        
    target_entity = get_object_or_404(Entity, id=target_entity_id)
    prior_entity_id = str(con.donor_entity.id) if con.donor_entity else "None"
    
    with transaction.atomic():
        con.donor_entity = target_entity
        con.review_status = ReviewStatus.VERIFIED
        con.save()
        
        # Log match attempt as overridden
        if con.match_attempt:
            con.match_attempt.match_method = "REVIEWER_OVERRIDDEN"
            con.match_attempt.selected_entity = target_entity
            con.match_attempt.reason = f"Rematched by reviewer. Reason: {reason}"
            con.match_attempt.save()
            
        # Record Audit Event
        AuditEvent.objects.create(
            action="MATCH_OVERRIDDEN",
            table_name="Contribution",
            record_id=str(con.id),
            prior_value={"donor_entity_id": prior_entity_id},
            new_value={"donor_entity_id": str(target_entity.id)},
            user=request.user if request.user.is_authenticated else None,
            reason=reason or "Reviewer rematched contribution to another entity."
        )
        
    return redirect('review_side_by_side', document_id=con.document.id)

@require_POST
def merge_entities(request, source_entity_id):
    source_entity = get_object_or_404(Entity, id=source_entity_id)
    target_entity_id = request.POST.get('target_entity')
    reason = request.POST.get('reason', '')
    
    if not target_entity_id:
        return HttpResponseBadRequest("Missing target_entity ID")
        
    target_entity = get_object_or_404(Entity, id=target_entity_id)
    
    with transaction.atomic():
        # Record merge relationship
        merge_rec = EntityMerge.objects.create(
            source_entity=source_entity,
            target_entity=target_entity,
            merged_by=request.user if request.user.is_authenticated else None,
            reason=reason
        )
        
        # Reassign all linked transactions of source to target
        contributions = Contribution.objects.filter(donor_entity=source_entity)
        for con in contributions:
            con.donor_entity = target_entity
            con.save()
            
        # Save source name as alias on target
        Alias.objects.get_or_create(
            entity=target_entity,
            alias_text=source_entity.canonical_name,
            defaults={
                'normalized_alias': source_entity.canonical_name.lower().strip(),
                'alias_type': 'MERGED_NAME'
            }
        )
        
        # Update source entity status to MERGED
        source_entity.status = EntityStatus.MERGED
        source_entity.save()
        
        # Record Audit Event
        AuditEvent.objects.create(
            action="ENTITY_MERGED",
            table_name="Entity",
            record_id=str(source_entity.id),
            prior_value={"status": source_entity.status},
            new_value={"status": "MERGED", "merged_into": str(target_entity.id)},
            user=request.user if request.user.is_authenticated else None,
            reason=reason or "Provisional entity merged into target entity."
        )
        
    # Find a document associated with the contributions to redirect back
    doc_id = request.POST.get('document_id')
    if doc_id:
        return redirect('review_side_by_side', document_id=doc_id)
    return redirect('document_queue')

@require_POST
def reverse_entity_merge(request, merge_id):
    merge_rec = get_object_or_404(EntityMerge, id=merge_id)
    
    if merge_rec.is_reversed:
        return HttpResponseBadRequest("Merge is already reversed")
        
    with transaction.atomic():
        # Restore source entity status
        source = merge_rec.source_entity
        source.status = EntityStatus.PROVISIONAL_AUTO_CREATED
        source.save()
        
        # Re-link transactions that originally belonged to source
        # (This is handled by scanning merge history or re-running prior linkings,
        # but to keep it simple, we link back contributions that were parsed under this source's name)
        contributions = Contribution.objects.filter(donor_entity=merge_rec.target_entity, donor_raw_name=source.canonical_name)
        for con in contributions:
            con.donor_entity = source
            con.save()
            
        # Mark merge record as reversed
        merge_rec.is_reversed = True
        merge_rec.save()
        
        # Record Audit Event
        AuditEvent.objects.create(
            action="MERGE_REVERSED",
            table_name="Entity",
            record_id=str(source.id),
            prior_value={"status": "MERGED"},
            new_value={"status": "PROVISIONAL_AUTO_CREATED"},
            user=request.user if request.user.is_authenticated else None,
            reason="Administrator reversed entity merge."
        )
        
    return redirect('document_queue')

@require_POST
def reject_contribution(request, contribution_id):
    con = get_object_or_404(Contribution, id=contribution_id)
    
    with transaction.atomic():
        con.review_status = ReviewStatus.REJECTED
        con.save()
        
        # Record Audit Event
        AuditEvent.objects.create(
            action="CONTRIBUTION_REJECTED",
            table_name="Contribution",
            record_id=str(con.id),
            prior_value={"review_status": "AUTO_IMPORTED"},
            new_value={"review_status": "REJECTED"},
            user=request.user if request.user.is_authenticated else None,
            reason="Reviewer rejected contribution."
        )
        
    return redirect('review_side_by_side', document_id=con.document.id)

@require_POST
def correct_contribution_fields(request, contribution_id):
    con = get_object_or_404(Contribution, id=contribution_id)
    
    name = request.POST.get('contributor_name')
    amount_str = request.POST.get('amount')
    date_str = request.POST.get('date')
    occupation = request.POST.get('occupation', '')
    employer = request.POST.get('employer', '')
    
    prior_val = {
        "donor_raw_name": con.donor_raw_name,
        "amount": str(con.amount),
        "transaction_date": str(con.transaction_date),
        "occupation": con.occupation,
        "employer": con.employer
    }
    
    with transaction.atomic():
        if name:
            con.donor_raw_name = name
        if amount_str:
            con.amount = float(amount_str.replace(",", "").replace("$", ""))
        if date_str:
            try:
                import datetime
                parts = date_str.split("/")
                if len(parts) == 3:
                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                    if year < 100:
                        year += 2000
                    con.transaction_date = datetime.date(year, month, day)
            except Exception:
                pass
        con.occupation = occupation
        con.employer = employer
        con.review_status = ReviewStatus.VERIFIED
        con.save()
        
        # Record Audit Event
        AuditEvent.objects.create(
            action="CONTRIBUTION_CORRECTED",
            table_name="Contribution",
            record_id=str(con.id),
            prior_value=prior_val,
            new_value={
                "donor_raw_name": con.donor_raw_name,
                "amount": str(con.amount),
                "transaction_date": str(con.transaction_date),
                "occupation": con.occupation,
                "employer": con.employer
            },
            user=request.user if request.user.is_authenticated else None,
            reason="Reviewer corrected contribution fields."
        )
        
    return redirect('review_side_by_side', document_id=con.document.id)

def review_queue(request):
    from apps.transactions.models import Contribution, ReviewStatus
    from apps.entities.models import Entity, EntityStatus
    from apps.assertions.models import Assertion, VerificationStatus
    from apps.research.models import EntityMatchCandidate
    
    # 1. Contributions needing review
    contribs = Contribution.objects.filter(review_status__in=[ReviewStatus.NEEDS_REVIEW, ReviewStatus.AUTO_IMPORTED, ReviewStatus.AUTO_MATCHED]).order_by('-transaction_date')
    
    # 2. Entity matches needing review
    matches = EntityMatchCandidate.objects.filter(status='PENDING').order_by('-match_score')
    
    # 3. Assertions needing review
    assertions = Assertion.objects.filter(verification_status__in=[VerificationStatus.UNVERIFIED, VerificationStatus.LEAD]).order_by('-created_at')
    
    # 4. Provisional entities needing verification
    provisional_entities = Entity.objects.filter(status=EntityStatus.PROVISIONAL_AUTO_CREATED).order_by('canonical_name')
    
    return render(request, 'extraction/review_queue.html', {
        'contributions': contribs[:50],
        'matches': matches[:50],
        'assertions': assertions[:50],
        'provisional_entities': provisional_entities[:50]
    })

def moderate_bulk_action(request):
    from django.shortcuts import redirect
    from apps.entities.models import Entity, EntityStatus
    from apps.assertions.models import Assertion, VerificationStatus
    from apps.transactions.models import Contribution, ReviewStatus, AuditEvent
    from apps.research.models import EntityMatchCandidate
    import random
    
    action = request.POST.get('action')
    record_type = request.POST.get('record_type')
    record_id = request.POST.get('record_id')
    
    user = request.user if request.user.is_authenticated else None
    user_name = user.username if user else "anonymous"
    
    if action == 'verify':
        if record_type == 'entity':
            ent = Entity.objects.get(id=record_id)
            old_status = ent.status
            ent.status = EntityStatus.VERIFIED
            ent.save()
            AuditEvent.objects.create(
                action="MODERATE",
                table_name="Entity",
                record_id=str(ent.id),
                prior_value={"status": old_status},
                new_value={"status": "VERIFIED"},
                user=user,
                reason=f"Quick verified entity '{ent.canonical_name}' by user '{user_name}'"
            )
        elif record_type == 'assertion':
            ast = Assertion.objects.get(id=record_id)
            old_status = ast.verification_status
            ast.verification_status = VerificationStatus.VERIFIED
            ast.save()
            AuditEvent.objects.create(
                action="MODERATE",
                table_name="Assertion",
                record_id=str(ast.id),
                prior_value={"verification_status": old_status},
                new_value={"verification_status": "VERIFIED"},
                user=user,
                reason=f"Quick verified assertion '{ast.public_id}' by user '{user_name}'"
            )
        elif record_type == 'contribution':
            con = Contribution.objects.get(id=record_id)
            old_status = con.review_status
            con.review_status = ReviewStatus.VERIFIED
            con.save()
            AuditEvent.objects.create(
                action="MODERATE",
                table_name="Contribution",
                record_id=str(con.id),
                prior_value={"review_status": old_status},
                new_value={"review_status": "VERIFIED"},
                user=user,
                reason=f"Quick verified contribution '{con.public_id}' by user '{user_name}'"
            )
        elif record_type == 'match':
            match = EntityMatchCandidate.objects.get(id=record_id)
            match.status = 'APPROVED'
            match.save()
            
    return redirect('review_queue')
