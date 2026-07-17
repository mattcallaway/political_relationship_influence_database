import pytest
from decimal import Decimal
import datetime
from django.test import Client
from apps.entities.models import Entity
from apps.campaigns.models import Campaign, Committee
from apps.transactions.models import Contribution, Expenditure
from apps.documents.models import Document, DocumentPage
from apps.sources.models import Source
from apps.assertions.models import Assertion
from apps.extraction.generic_parsers import parse_form_410, parse_form_496, parse_form_497

@pytest.mark.django_db
def test_parse_form_410():
    # Setup source and document
    src = Source.objects.create(public_id="SRC410", title="Form 410 Statement of Organization")
    doc = Document.objects.create(original_filename="statement_410.pdf", source=src)
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text="""
        STATEMENT OF ORGANIZATION - FORM 410
        Committee Name: Committee to Elect Gore
        Filer ID: 987654
        Name of Treasurer: Jane Treasurer Smith
        Controlled Candidate: James Gore
        """
    )
    
    parse_form_410(doc, src)
    
    # Assert committee profile is created
    committee = Committee.objects.filter(fppc_id="987654").first()
    assert committee is not None
    assert committee.committee_name == "Committee to Elect Gore"
    assert committee.treasurer_name == "Jane Treasurer Smith"
    
    # Assert candidate was linked
    assert committee.controlling_candidate is not None
    assert committee.controlling_candidate.canonical_name == "James Gore"
    
    # Assert assertions created
    assert Assertion.objects.filter(predicate='TREASURER_FOR').exists()
    assert Assertion.objects.filter(predicate='CONTROLS').exists()

@pytest.mark.django_db
def test_parse_form_496():
    src = Source.objects.create(public_id="SRC496", title="Form 496 Report")
    doc = Document.objects.create(original_filename="independent_exp_496.pdf", source=src)
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text="""
        LATE INDEPENDENT EXPENDITURE REPORT - FORM 496
        Filer: Working Families for Sonoma County
        Candidate Name: James Gore
        Support/Oppose: OPPOSE
        Payee: Muelrath Public Affairs
        Date of Expenditure: 10/15/2026
        Amount: 3200.00
        Description: Mailers opposing James Gore
        """
    )
    
    parse_form_496(doc, src)
    
    exp = Expenditure.objects.filter(schedule="Form 496").first()
    assert exp is not None
    assert exp.is_independent_expenditure is True
    assert exp.support_oppose == "OPPOSE"
    assert exp.amount == Decimal("3200.00")
    assert exp.payee_entity.canonical_name == "Muelrath Public Affairs"
    assert exp.campaign.candidate.canonical_name == "James Gore"

@pytest.mark.django_db
def test_parse_form_497():
    src = Source.objects.create(public_id="SRC497", title="Form 497 Report")
    doc = Document.objects.create(original_filename="late_contrib_497.pdf", source=src)
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text="""
        LATE CONTRIBUTION REPORT - FORM 497
        Filer: Sonoma County Development Corp Pac
        Recipient: Friends of James Gore
        Date of Contribution: 10/18/2026
        Amount: 1500.00
        """
    )
    
    parse_form_497(doc, src)
    
    con = Contribution.objects.filter(schedule="Form 497").first()
    assert con is not None
    assert con.amount == Decimal("1500.00")
    assert con.donor_entity.canonical_name == "Sonoma County Development Corp Pac"
    assert con.filer_committee.canonical_name == "Friends of James Gore"
