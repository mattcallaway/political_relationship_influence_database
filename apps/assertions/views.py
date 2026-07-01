from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import uuid
from apps.entities.models import Entity
from apps.sources.models import Source, SourceLocator
from apps.assertions.models import Assertion, AssertionSource, PredicateVocabulary, ClaimType, VerificationStatus, SupportType

def assertion_list(request):
    assertions = Assertion.objects.all().order_by('-created_at')
    return render(request, 'assertions/assertion_list.html', {
        'assertions': assertions[:100]
    })

def create_assertion(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_entity')
        predicate = request.POST.get('predicate')
        object_id = request.POST.get('object_entity')
        object_value = request.POST.get('object_value', '')
        claim_type = request.POST.get('claim_type', 'FACTUAL')
        effective_start = request.POST.get('effective_start') or None
        effective_end = request.POST.get('effective_end') or None
        jurisdiction = request.POST.get('jurisdiction', 'Sonoma County')
        sensitive_claim = request.POST.get('sensitive_claim') == 'true'
        explanatory_note = request.POST.get('explanatory_note', '')
        
        source_id = request.POST.get('source')
        page_num = request.POST.get('page_num', '')
        section = request.POST.get('section', '')
        evidence_note = request.POST.get('evidence_note', '')
        
        subject = get_object_or_404(Entity, id=subject_id)
        obj_ent = Entity.objects.filter(id=object_id).first() if object_id else None
        
        assertion = Assertion.objects.create(
            public_id=f"AST-{uuid.uuid4().hex[:8].upper()}",
            subject_entity=subject,
            predicate=predicate,
            object_entity=obj_ent,
            object_value=object_value,
            claim_type=claim_type,
            effective_start=effective_start,
            effective_end=effective_end,
            jurisdiction=jurisdiction,
            sensitive_claim=sensitive_claim,
            explanatory_note=explanatory_note
        )
        
        if source_id:
            source = get_object_or_404(Source, id=source_id)
            locator = SourceLocator.objects.create(
                source=source,
                section=section,
                page_range=page_num
            )
            AssertionSource.objects.create(
                assertion=assertion,
                source=source,
                source_locator=locator,
                concise_evidence_note=evidence_note,
                evidence_note=evidence_note
            )
            
        messages.success(request, "Assertion created successfully!")
        return redirect('assertion_list')
        
    entities = Entity.objects.all().order_by('canonical_name')
    sources = Source.objects.all().order_by('title')
    vocab = PredicateVocabulary.objects.all().order_by('label')
    return render(request, 'assertions/assertion_create.html', {
        'entities': entities,
        'sources': sources,
        'predicates': vocab,
        'claim_types': ClaimType.choices
    })

def edit_assertion(request, assertion_id):
    assertion = get_object_or_404(Assertion, id=assertion_id)
    if request.method == 'POST':
        assertion.predicate = request.POST.get('predicate')
        object_id = request.POST.get('object_entity')
        assertion.object_entity = Entity.objects.filter(id=object_id).first() if object_id else None
        assertion.object_value = request.POST.get('object_value', '')
        assertion.claim_type = request.POST.get('claim_type', 'FACTUAL')
        assertion.effective_start = request.POST.get('effective_start') or None
        assertion.effective_end = request.POST.get('effective_end') or None
        assertion.jurisdiction = request.POST.get('jurisdiction', 'Sonoma County')
        assertion.sensitive_claim = request.POST.get('sensitive_claim') == 'true'
        assertion.explanatory_note = request.POST.get('explanatory_note', '')
        assertion.save()
        
        messages.success(request, "Assertion updated successfully!")
        return redirect('assertion_list')
        
    entities = Entity.objects.all().order_by('canonical_name')
    vocab = PredicateVocabulary.objects.all().order_by('label')
    return render(request, 'assertions/assertion_edit.html', {
        'assertion': assertion,
        'entities': entities,
        'predicates': vocab,
        'claim_types': ClaimType.choices
    })
