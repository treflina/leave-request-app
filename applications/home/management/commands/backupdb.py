import os
import subprocess
import datetime
import gzip
import shutil
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """"Backup DB (MySQL/Postgres/SQLite),
        compress it, and send to remote server."""

    def handle(self, *args, **options):

        # REMOTE_ENABLED = True
        # REMOTE_USER = ""
        # REMOTE_HOST = ""
        # REMOTE_PATH = "/remote/backups/"

        db_settings = settings.DATABASES["default"]
        engine = db_settings["ENGINE"]
        db_name = db_settings["NAME"]
        db_user = db_settings.get("USER", "")
        db_pass = db_settings.get("PASSWORD", "")
        db_host = db_settings.get("HOST", "")
        db_port = db_settings.get("PORT", "")

        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        sql_backup_path = os.path.join(
            backup_dir, f"{db_name}_backup_{date_str}.sql"
            )
        compressed_backup_path = sql_backup_path + ".gz"

        if "mysql" in engine:
            backup_command = [
                "mysqldump",
                f"-u{db_user}",
                f"-h{db_host or 'localhost'}",
                f"-P{db_port or '3306'}",
                "--single-transaction",
                "--routines",
                "--triggers",
                "--no-tablespaces",
                db_name,
            ]
            os.environ["MYSQL_PWD"] = db_pass

        elif "postgresql" in engine:
            backup_command = [
                "pg_dump",
                "-h", db_host or "localhost",
                "-p", db_port or "5432",
                "-U", db_user,
                db_name,
            ]
            os.environ["PGPASSWORD"] = db_pass
        elif "sqlite3" in engine:
            self.stdout.write(
                self.style.WARNING("Backing up SQLite database...")
                )
            shutil.copy(db_name, sql_backup_path)
            backup_command = None
        else:
            self.stderr.write(self.style.ERROR(
                f"Unsupported database engine: {engine}")
                )
            return

        try:
            if backup_command:
                self.stdout.write(self.style.WARNING(
                    f"Backing up {engine} database '{db_name}'...")
                    )
                with open(sql_backup_path, "w") as out:
                    subprocess.run(backup_command, stdout=out, check=True)

            with open(sql_backup_path, "rb") as f_in:
                with gzip.open(compressed_backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(sql_backup_path)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Backup created: {compressed_backup_path}"
                    )
                )

        except subprocess.CalledProcessError as e:
            self.stderr.write(self.style.ERROR(f"Backup failed: {e}"))
            return

        # if REMOTE_ENABLED:
        #     try:
        #         self.stdout.write(self.style.WARNING(
        # "Uploading backup to remote server..."))
        #         subprocess.run([
        #             "scp",
        #             compressed_backup_path,
        #             f"{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}"
        #         ], check=True)
        #         self.stdout.write(
        #           self.style.SUCCESS(
        #               f"Uploaded to {REMOTE_HOST}:{REMOTE_PATH}"))
        #     except subprocess.CalledProcessError as e:
        #         self.stderr.write(self.style.ERROR(f"Upload failed: {e}"))

        retention_days = 15
        cutoff_date = datetime.datetime.now() - datetime.timedelta(
            days=retention_days
            )
        deleted_count = 0
        for filename in os.listdir(backup_dir):
            if filename.endswith(".gz"):
                file_path = os.path.join(backup_dir, filename)
                file_time = datetime.datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                    )
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
        if deleted_count:
            self.stdout.write(self.style.WARNING(
                f"🧹 Deleted {deleted_count} old backup(s).")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("No old backups to delete.")
                )
