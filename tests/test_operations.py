import os
import pytest
import io
import glob
from django.core.management import call_command
from django.conf import settings
from apps.audit.models import ImportBatch, LegacyIdentifier
from apps.entities.models import Entity, EntityStatus
from apps.transactions.models import Contribution, Expenditure

@pytest.mark.django_db
def test_database_backup_command(settings):
    import tempfile
    import shutil
    
    # Create temp directory and fake db file
    temp_dir = tempfile.mkdtemp()
    fake_db = os.path.join(temp_dir, "fake_db.sqlite3")
    with open(fake_db, "w") as f:
        f.write("sqlite database placeholder")
        
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': fake_db
    }
    
    # Run the backup command
    out = io.StringIO()
    call_command('database_backup', stdout=out)
    output = out.getvalue()
    assert "integrity check passed" in output
    assert "Backup created successfully" in output

    backup_dir = os.path.join(temp_dir, 'backups')
    assert os.path.exists(backup_dir)
    
    files = glob.glob(os.path.join(backup_dir, 'db_backup_*.sqlite3'))
    assert len(files) == 1

    # Test pruning logic by creating 6 fake backup files and running command again
    for i in range(6):
        fake_path = os.path.join(backup_dir, f"db_backup_20260701_00000{i}.sqlite3")
        with open(fake_path, 'w') as f:
            f.write("fake backup")
    
    # Run backup again
    call_command('database_backup', stdout=out)
    
    # Assert backups folder size has pruned down to exactly 5 backups
    files_after = glob.glob(os.path.join(backup_dir, 'db_backup_*.sqlite3'))
    assert len(files_after) == 5

    # Clean up temp dir
    shutil.rmtree(temp_dir)

@pytest.mark.django_db
def test_rollback_import_command():
    # Setup batch
    batch = ImportBatch.objects.create(
        batch_name="Test Import Batch",
        source_file="test_import.csv",
        status="SUCCESS"
    )

    # Setup entities and transactions
    filer = Entity.objects.create(public_id='ENT_FIL_9', canonical_name='Filer Committee', entity_type='COMMITTEE')
    prov_ent = Entity.objects.create(public_id='ENT_PRV_9', canonical_name='Provisional Filer', entity_type='PERSON', status=EntityStatus.PROVISIONAL_AUTO_CREATED)
    
    Contribution.objects.create(
        public_id='CON_TEST_9',
        filer_committee=filer,
        donor_entity=prov_ent,
        donor_raw_name='Provisional Filer',
        amount=100.00,
        transaction_date='2026-07-01',
        import_batch=batch
    )

    # Legacy ID link
    LegacyIdentifier.objects.create(
        legacy_id='LEGACY_9',
        current_public_id=prov_ent.public_id,
        target_model='Entity',
        entity=prov_ent,
        import_batch=batch
    )

    assert Contribution.objects.filter(import_batch=batch).count() == 1
    assert Entity.objects.filter(public_id='ENT_PRV_9').exists()

    # Call rollback command
    out = io.StringIO()
    call_command('rollback_import', str(batch.id), stdout=out)
    
    # Reload and assert deletions
    batch.refresh_from_db()
    assert batch.status == 'ROLLED_BACK'
    assert Contribution.objects.filter(import_batch=batch).count() == 0
    # Provisional entity has no other references, so it should be deleted!
    assert not Entity.objects.filter(public_id='ENT_PRV_9').exists()
