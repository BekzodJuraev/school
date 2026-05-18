"""
Management command: sync_turniket

Usage:
    python manage.py sync_turniket --file turniket_id.xlsx

What it does:
    1. Reads employee IDs from the 'id' column in Excel
    2. For each ID, fetches name + photo from Hikvision camera
    3. All records from this file are role='worker'
    4. Saves/updates Turniket records in Django DB
"""

import requests
import pandas as pd
from requests.auth import HTTPDigestAuth
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from pathlib import Path

from application.models import Turniket

# ── Camera config ──────────────────────────────────────────────────────────────
CAM_IP     = "192.168.1.178"
CAM_AUTH   = HTTPDigestAuth("admin", "Abc2025@")
SEARCH_URL = f"http://{CAM_IP}/ISAPI/AccessControl/UserInfo/Search?format=json"


def fetch_user_from_camera(emp_id: str):
    """Fetch user info from Hikvision by employee ID. Returns dict or None."""
    payload = {
        "UserInfoSearchCond": {
            "searchID": "1",
            "maxResults": 1,
            "searchResultPosition": 0,
            "EmployeeNoList": [{"employeeNo": emp_id}],
        }
    }
    try:
        resp = requests.post(SEARCH_URL, auth=CAM_AUTH, json=payload, timeout=10)
        resp.raise_for_status()
        users = resp.json().get("UserInfoSearch", {}).get("UserInfo", [])
        return users[0] if users else None
    except Exception as e:
        return None


def fetch_photo(face_url: str):
    """Download face photo bytes from camera. Returns bytes or None."""
    if not face_url:
        return None
    try:
        url = f"http://{CAM_IP}{face_url}" if face_url.startswith("/") else face_url
        resp = requests.get(url, auth=CAM_AUTH, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


class Command(BaseCommand):
    help = "Sync worker IDs from turniket_id.xlsx → Hikvision camera → Turniket DB"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, required=True, help="Path to Excel file")
        parser.add_argument("--dry-run", action="store_true", help="Preview without saving")

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run   = options["dry_run"]

        # ── 1. Read Excel ──────────────────────────────────────────────────────
        if not Path(file_path).exists():
            raise CommandError(f"File not found: {file_path}")

        # dtype=str keeps leading zeros (00000004 stays '00000004')
        df = pd.read_excel(file_path, dtype=str)

        if "id" not in df.columns:
            raise CommandError(f"Expected column 'id' but found: {list(df.columns)}")

        ids = df["id"].dropna().str.strip().unique().tolist()

        self.stdout.write(self.style.SUCCESS(f"Found {len(ids)} IDs in Excel\n"))
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be saved\n"))

        # ── 2. Sync each ID ────────────────────────────────────────────────────
        created = updated = skipped = failed = 0

        for emp_id in ids:
            self.stdout.write(f"  [{emp_id}] ", ending="")

            user = fetch_user_from_camera(emp_id)
            if not user:
                self.stdout.write(self.style.ERROR("not found on camera"))
                failed += 1
                continue

            name     = (user.get("name") or "").strip() or f"Worker {emp_id}"
            face_url = user.get("faceURL", "")

            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f"{name} | worker | photo={'yes' if face_url else 'no'}"
                ))
                continue

            # user_id: strip leading zeros for IntegerField
            user_id = int(emp_id)

            obj, is_new = Turniket.objects.get_or_create(
                user_id=user_id,
                defaults={"name": name, "role": "worker"},
            )

            changed = False

            if obj.name != name:
                obj.name = name
                changed = True

            # Download and save photo only if not already set
            if face_url and not obj.photo:
                photo_bytes = fetch_photo(face_url)
                if photo_bytes:
                    obj.photo.save(f"{emp_id}.jpg", ContentFile(photo_bytes), save=False)
                    changed = True

            if is_new or changed:
                obj.save()
                label = "CREATED" if is_new else "UPDATED"
                self.stdout.write(self.style.SUCCESS(f"{name} → {label}"))
                if is_new:
                    created += 1
                else:
                    updated += 1
            else:
                self.stdout.write(f"{name} → no change")
                skipped += 1

        # ── 3. Summary ─────────────────────────────────────────────────────────
        self.stdout.write("\n" + "─" * 45)
        self.stdout.write(self.style.SUCCESS(f"  Created : {created}"))
        self.stdout.write(self.style.WARNING(f"  Updated : {updated}"))
        self.stdout.write(f"  Skipped : {skipped}")
        self.stdout.write(self.style.ERROR(f"  Failed  : {failed} (not on camera)"))
        self.stdout.write("─" * 45)