import os
import shutil
import glob
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection

class Command(BaseCommand):
    help = "Performs a database health integrity check and saves a timestamped backup."

    def handle(self, *args, **options):
        # 1. Run Integrity Check
        self.stdout.write("Running database health integrity check...")
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if not row or row[0] != "ok":
                raise CommandError(f"Database integrity check failed: {row}")
        self.stdout.write(self.style.SUCCESS("Database integrity check passed successfully!"))

        # 2. Get SQLite database file path
        db_config = settings.DATABASES['default']
        if db_config['ENGINE'] != 'django.db.backends.sqlite3':
            self.stdout.write(self.style.WARNING("Non-SQLite database detected. Skipping file-copy backup."))
            return

        db_file = db_config['NAME']
        
        # Check for in-memory databases (common in test suites)
        if ':memory:' in db_file or 'memorydb' in db_file or not os.path.exists(db_file):
            self.stdout.write(self.style.WARNING("In-memory SQLite database or missing file detected. Skipping file copy."))
            return

        # Resolve absolute path for SQLite file
        if not os.path.isabs(db_file):
            db_file = os.path.abspath(db_file)

        # 3. Create backup directory in workspace
        workspace_dir = os.path.dirname(db_file)
        backup_dir = os.path.join(workspace_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # 4. Generate timestamped file copy
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"db_backup_{timestamp}.sqlite3"
        backup_path = os.path.join(backup_dir, backup_filename)

        shutil.copy2(db_file, backup_path)
        self.stdout.write(self.style.SUCCESS(f"Backup created successfully at: {backup_path}"))

        # 5. Prune backups to keep only the 5 most recent
        backups = sorted(glob.glob(os.path.join(backup_dir, "db_backup_*.sqlite3")))
        if len(backups) > 5:
            to_delete = backups[:-5]
            for file_path in to_delete:
                os.remove(file_path)
                self.stdout.write(f"Pruned old backup file: {os.path.basename(file_path)}")
