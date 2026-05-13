import json
from pathlib import Path

from django.core.management.base import BaseCommand
from animals.models import Animal, AnimalLocation


class Command(BaseCommand):
    help = "Import animal distribution map points from JSON"

    def handle(self, *args, **kwargs):
        file_path = Path("data/search_wilds_animal_distribution_50.json")

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for item in data:
            animal_name = item.get("name", "").strip()

            if not animal_name:
                skipped_count += 1
                continue

            try:
                animal = Animal.objects.get(name__iexact=animal_name)
            except Animal.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Animal not found: {animal_name}")
                )
                skipped_count += 1
                continue

            countries = item.get("countries", [])
            default_country = countries[0] if countries else ""

            map_points = item.get("map_points", [])

            for point in map_points:
                place_name = point.get("label", "").strip()
                latitude = point.get("lat")
                longitude = point.get("lng")

                if not place_name or latitude is None or longitude is None:
                    skipped_count += 1
                    continue

                # Use country from point if available, otherwise use first country from countries list
                country = point.get("country", default_country)

                location, created = AnimalLocation.objects.update_or_create(
                    animal=animal,
                    place_name=place_name,
                    defaults={
                        "country": country,
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )