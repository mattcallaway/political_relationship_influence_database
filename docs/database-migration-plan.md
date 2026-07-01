# Database Migration Plan: Sonoma Civic Research Platform

This document describes the step-by-step procedure to migrate the database schema and existing campaign-finance data (Milestone 1) to support the expanded five-layer civic-research architecture (Milestone 2).

---

## 1. Backup Strategy
Before executing any structural database migrations, a complete snapshot of the database must be preserved.
* **SQLite (Local Development)**:
  Copy `db.sqlite3` to a secure backup directory inside the scratch workspace:
  ```powershell
  Copy-Item db.sqlite3 -Destination "C:\Users\Mathew C\.gemini\antigravity\brain\d17a0fbd-d4f2-48ad-bc2f-d5891373e2b7\scratch\db_backup_pre_expansion.sqlite3"
  ```
* **PostgreSQL (Production)**:
  Perform a pg_dump:
  ```bash
  pg_dump -U username -d dbname -F c -b -v -f data/backups/pre_expansion_backup.dump
  ```

---

## 2. Phase-by-Phase Schema Migrations

### Phase A: Additive Schema Changes (No Destructive Alters)
Run migrations to register the new models and subtype tables:
1. **Layer 1 Addition**: Create `SourceLocator` and expand `Source`, `Document`, and `DocumentPage` fields.
2. **Layer 2 Subtypes**: Add Entity types to `EntityType` choices, increase status string size to `50` characters, and create subtype tables (`Person`, `Organization`, `Campaign`, `Committee`, `BallotMeasure`, `Project`, `GovernmentBody`, `PublicOffice`).
3. **Layer 3 Action Transactions**: Create `Expenditure`, `Contract`, `LobbyingActivity`, `Appointment`, `Meeting`, `AgendaItem`, `Motion`, `Vote`, `PublicComment`, `ProjectAction`.
4. **Layer 4 Assertion Infrastructure**: Setup `Assertion` and `AssertionSource` models.
5. **Layer 5 Workflow Operations**: Register `ResearchCollection`, `ResearchTask`, `PRARequest`.

---

## 3. Data Migration (Choice Mapping & Normalization)

A custom Django data migration must run to map old status choices to the new expanded options.

### Status Mappings:
* **`Entity.status`**:
  * `'PROPOSED'` $\rightarrow$ `'PROVISIONAL_AUTO_CREATED'`
  * `'APPROVED'` $\rightarrow$ `'VERIFIED'`
* **`Contribution.review_status`**:
  * `'PROPOSED'` $\rightarrow$ `'AUTO_IMPORTED'`
  * `'APPROVED'` $\rightarrow$ `'VERIFIED'`
  * `'CORRECTED'` $\rightarrow$ `'VERIFIED'` (reviewer corrections will carry verified status flags)

### Django Data Migration Script Outline (`0003_migrate_existing_statuses.py`):
```python
from django.db import migrations

def map_statuses(apps, schema_editor):
    Entity = apps.get_model('entities', 'Entity')
    Contribution = apps.get_model('transactions', 'Contribution')
    
    # Update Entities
    for ent in Entity.objects.all():
        if ent.status == 'PROPOSED':
            ent.status = 'PROVISIONAL_AUTO_CREATED'
            ent.save()
        elif ent.status == 'APPROVED':
            ent.status = 'VERIFIED'
            ent.save()
            
    # Update Contributions
    for con in Contribution.objects.all():
        if con.review_status == 'PROPOSED':
            con.review_status = 'AUTO_IMPORTED'
            con.save()
        elif con.review_status in ('APPROVED', 'CORRECTED'):
            con.review_status = 'VERIFIED'
            con.save()

class Migration(migrations.Migration):
    dependencies = [
        ('entities', '0002_alter_entity_status_entitymerge'),
        ('transactions', '0002_contribution_document_contribution_extracted_block_and_more'),
    ]
    operations = [
        migrations.RunPython(map_statuses),
    ]
```

---

## 4. Verification and Rollback Strategy

### Count-Verification Script
Run the verification check before and after migrating:
```python
# check_counts.py
from apps.entities.models import Entity
from apps.transactions.models import Contribution

print(f"Entities Count: {Entity.objects.count()}")
print(f"Contributions Count: {Contribution.objects.count()}")
```

### Rollback Plan
If any step during the migration fails:
1. **Stop execution** immediately.
2. **Restore backup**:
   * SQLite: Replace `db.sqlite3` with `db_backup_pre_expansion.sqlite3`.
   * Postgres: Run pg_restore.
3. **Verify functionality**: Run `pytest` to confirm that the Milestone 1 codebase is fully functional.
