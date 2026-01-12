import requests
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import get_user_model

from jobs.models import Job


class Command(BaseCommand):
    help = "Import jobs from Arbeitnow Job Board API into local database."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200, help="Max number of jobs to import (default: 200)")
        parser.add_argument("--visa_sponsorship", choices=["true", "false"], default=None,
                            help="Optional: filter visa sponsorship if supported by API URL param")
        parser.add_argument("--dry_run", action="store_true", help="Do not write to DB, just show counts")

    def handle(self, *args, **options):
        limit = max(1, int(options["limit"]))
        visa = options.get("visa_sponsorship")
        dry_run = options["dry_run"]

        api_url = settings.ARBEITNOW_API_URL
        if visa:
            joiner = "&" if "?" in api_url else "?"
            api_url = f"{api_url}{joiner}visa_sponsorship={visa}"

        self.stdout.write(self.style.NOTICE(f"Fetching: {api_url}"))
        try:
            resp = requests.get(
                api_url,
                timeout=25,
                headers={"User-Agent": "JobPortalStudentProject/1.0"}
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"API fetch failed: {e}"))
            return

        data = payload.get("data", [])
        if not isinstance(data, list):
            self.stderr.write(self.style.ERROR("Unexpected API response: 'data' is not a list"))
            return

        data = data[:limit]

        # Create/get an importer employer user
        User = get_user_model()
        importer, created = User.objects.get_or_create(
            username="api_importer",
            defaults={
                "email": "api_importer@example.com",
                "role": "employer",
                "company_name": "API Importer",
                "is_active": True,
            }
        )
        if created:
            importer.set_unusable_password()
            importer.save(update_fields=["password"])

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for item in data:
            try:
                slug = (item.get("slug") or "").strip()
                title = (item.get("title") or "").strip()
                company_name = (item.get("company_name") or "").strip()
                location = (item.get("location") or "").strip()
                remote = bool(item.get("remote", False))
                url = (item.get("url") or "").strip()
                tags = item.get("tags") or []
                category = tags[0] if isinstance(tags, list) and tags else "Other"

                # Description is HTML-ish in API; store as plain text
                desc_html = item.get("description") or ""
                description = strip_tags(desc_html).strip()

                # Unix timestamp -> aware datetime
                ext_ts = item.get("created_at")
                ext_dt = None
                if isinstance(ext_ts, int):
                    ext_dt = datetime.fromtimestamp(ext_ts, tz=dt_timezone.utc)
                    ext_dt = timezone.localtime(ext_dt)

                if not slug or not title or not company_name:
                    skipped_count += 1
                    continue

                defaults = dict(
                    title=title,
                    description=description or "No description provided.",
                    company=company_name,
                    category=category,
                    location=location or ("Remote" if remote else "Unknown"),
                    salary=None,
                    employer=importer,
                    is_active=True,
                    is_external=True,
                    external_url=url or None,
                    remote=remote,
                    external_created_at=ext_dt,
                )

                if dry_run:
                    # Just count it as would-be created/updated
                    exists = Job.objects.filter(external_source="arbeitnow", external_id=slug).exists()
                    created_count += 0 if exists else 1
                    updated_count += 1 if exists else 0
                    continue

                obj, was_created = Job.objects.update_or_create(
                    external_source="arbeitnow",
                    external_id=slug,
                    defaults=defaults
                )
                if was_created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception:
                skipped_count += 1
                continue

        self.stdout.write(self.style.SUCCESS("Import finished."))
        self.stdout.write(f"Created: {created_count}")
        self.stdout.write(f"Updated: {updated_count}")
        self.stdout.write(f"Skipped: {skipped_count}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: no DB changes were made."))
