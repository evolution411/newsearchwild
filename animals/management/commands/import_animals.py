import json
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from animals.models import Animal, AnimalCategory


def get_wikipedia_data(wiki_title):
    if not wiki_title:
        return "", "", ""

    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"

    try:
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            return "", "", ""

        data = response.json()

        summary = data.get("extract", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

        image_url = ""

        if "thumbnail" in data:
            image_url = data["thumbnail"].get("source", "")
        elif "originalimage" in data:
            image_url = data["originalimage"].get("source", "")

        return summary, image_url, page_url

    except requests.RequestException:
        return "", "", ""


class Command(BaseCommand):
    help = "Import animals from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/search_wilds_50_animals.json",
            help="Path to the animal JSON file"
        )

    def handle(self, *args, **kwargs):
        file_path = Path(kwargs["file"])

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as file:
            animals = json.load(file)

        created_count = 0
        updated_count = 0

        for item in animals:
            name = item.get("name", "").strip()

            if not name:
                continue

            category_name = item.get("category", "Unknown") or "Unknown"

            category, _ = AnimalCategory.objects.get_or_create(
                name=category_name
            )

            habitats = item.get("habitats", [])
            habitat = ""

            if isinstance(habitats, list) and len(habitats) > 0:
                habitat = habitats[0]
            elif isinstance(habitats, str):
                habitat = habitats

            wiki_title = item.get("wiki_title", "")
            wiki_summary, wiki_image_url, wiki_page_url = get_wikipedia_data(wiki_title)

            animal, created = Animal.objects.update_or_create(
                name=name,
                defaults={
                    "scientific_name": item.get("scientific_name", ""),
                    "category": category,
                    "habitat": habitat,
                    "diet": item.get("diet", ""),
                    "conservation_status": item.get("conservation_status", "Unknown"),
                    "description": item.get("description", ""),
                    "fun_fact": item.get("fun_fact", ""),

                    "wiki_title": wiki_title,
                    "wiki_summary": wiki_summary,
                    "wiki_image_url": wiki_image_url,
                    "wiki_page_url": wiki_page_url,

                    # Remove these two lines if your model does not have these fields
                    "countries": item.get("countries", []),
                    "map_points": item.get("map_points", []),
                },
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Updated: {name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete. Created: {created_count}, Updated: {updated_count}"
            )
        )
