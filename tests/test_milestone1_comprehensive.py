import pytest
import json
import io
from django.core.management import call_command
from django.test import Client
from django.db import connection
from django.test.utils import CaptureQueriesContext
from apps.entities.models import Entity, Person, Organization
from apps.sources.models import Source
from apps.transactions.models import Expenditure, Contribution
from apps.research.models import ResearchCollection, DataQualityIssue, OpenQuestion

@pytest.mark.django_db
def test_database_inventory_report_command():
    # Test Markdown/text output
    out = io.StringIO()
    call_command('database_inventory_report', markdown=True, include_quality_checks=True, stdout=out)
    output = out.getvalue()
    assert "Model Counts" in output
    assert "Entities" in output
    
    # Test JSON output
    out_json = io.StringIO()
    call_command('database_inventory_report', json=True, include_quality_checks=True, stdout=out_json)
    output_json = json.loads(out_json.getvalue())
    assert "counts" in output_json
    assert "entities" in output_json["counts"]
    assert "quality_checks" in output_json

@pytest.mark.django_db
def test_expenditure_creation_and_reconciliation():
    filer = Entity.objects.create(public_id='ENT0001', canonical_name='Test Filer Committee', entity_type='COMMITTEE')
    payee = Entity.objects.create(public_id='ENT0002', canonical_name='Test Payee Corp', entity_type='ORGANIZATION')
    source = Source.objects.create(public_id='SRC0001', title='Test Source Publication')
    
    exp = Expenditure.objects.create(
        public_id='EXP0001',
        filer_committee=filer,
        payee_entity=payee,
        payee_raw_name='Test Payee Corp',
        amount=1500.00,
        transaction_date='2026-07-01',
        transaction_code='CNS',
        source=source,
        description='Campaign consulting services'
    )
    
    assert exp.amount == 1500.00
    assert exp.source.title == 'Test Source Publication'
    assert exp.payee_entity.canonical_name == 'Test Payee Corp'

@pytest.mark.django_db
def test_data_quality_issues_logging():
    # Create invalid amount contribution to trigger warning
    filer = Entity.objects.create(public_id='ENT0003', canonical_name='Filer', entity_type='COMMITTEE')
    Contribution.objects.create(
        public_id='CON0001',
        filer_committee=filer,
        donor_raw_name='Donor',
        amount=-50.00,  # Invalid amount
        transaction_date='2026-07-01'
    )
    
    # Run quality scan via view call
    client = Client()
    response = client.get('/research/data-quality/')
    assert response.status_code == 200
    
    # Check if data quality warning is created
    dq_issues = DataQualityIssue.objects.filter(issue_type="Invalid Amount")
    assert dq_issues.count() > 0
    assert "negative amount" in dq_issues.first().description

@pytest.mark.django_db
def test_query_count_performance():
    client = Client()
    
    # 1. Test Dashboard query performance
    with CaptureQueriesContext(connection) as ctx:
        client.get('/research/')
    assert len(ctx.captured_queries) < 60
    
    # 2. Test Entity Detail query performance
    ent = Entity.objects.create(public_id='P123456', canonical_name='Test Person', entity_type='PERSON')
    with CaptureQueriesContext(connection) as ctx_detail:
        client.get(f'/entity/{ent.public_id}/')
    assert len(ctx_detail.captured_queries) < 60
