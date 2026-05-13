import json
from pathlib import Path

from django.core.management.base import BaseCommand
from animals.models import Animal


class Command(BaseCommand):
    help = "Import animal lifespan, size, and natural enemies"

    def handle(self, *args, **kwargs):
        file_path = Path("data/search_wilds_lifespan_size_enemies_50.json")

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        updated_count = 0
        skipped_count = 0

        for item in data:
            name = item.get("name", "").strip()

            if not name:
                skipped_count += 1
                continue

            try:
                animal = Animal.objects.get(name__iexact=name)
            except Animal.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Animal not found: {name}"))
                skipped_count += 1
                continue

            animal.lifespan = item.get("lifespan", "")
            animal.size = item.get("size", "")
            animal.natural_enemies = item.get("natural_enemies", [])
            animal.save()

            updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )