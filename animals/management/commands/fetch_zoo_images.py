from django.core.management.base import BaseCommand

from animals.models import Zoo
from animals.wiki_api import fetch_wikipedia_summary


ZOO_WIKIPEDIA_TITLES = {
    "ABQ BioPark": "ABQ BioPark",
    "Adventure Aquarium": "Adventure Aquarium",
    "Alaska SeaLife Center": "Alaska SeaLife Center",
    "Audubon Zoo": "Audubon Zoo",
    "Birmingham Zoo": "Birmingham Zoo",
    "Blank Park Zoo": "Blank Park Zoo",
    "Brandywine Zoo": "Brandywine Zoo",
    "Bronx Zoo": "Bronx Zoo",
    "Brookfield Zoo Chicago": "Brookfield Zoo",
    "Central Park Zoo": "Central Park Zoo",
    "Columbus Zoo and Aquarium": "Columbus Zoo and Aquarium",
    "Dakota Zoo": "Dakota Zoo",
    "Dallas Zoo": "Dallas Zoo",
    "Denver Zoo Conservation Alliance": "Denver Zoo",
    "Detroit Zoo": "Detroit Zoo",
    "ECHO, Leahy Center for Lake Champlain": "ECHO, Leahy Center for Lake Champlain",
    "Franklin Park Zoo": "Franklin Park Zoo",
    "Great Plains Zoo": "Great Plains Zoo",
    "Hattiesburg Zoo": "Hattiesburg Zoo",
    "Honolulu Zoo": "Honolulu Zoo",
    "Houston Zoo": "Houston Zoo",
    "Indianapolis Zoo": "Indianapolis Zoo",
    "Lincoln Park Zoo": "Lincoln Park Zoo",
    "Little Rock Zoo": "Little Rock Zoo",
    "Living Shores Aquarium": "Living Shores Aquarium",
    "Los Angeles Zoo": "Los Angeles Zoo",
    "Louisville Zoo": "Louisville Zoo",
    "Maine State Aquarium": "Maine State Aquarium",
    "Milwaukee County Zoo": "Milwaukee County Zoo",
    "Minnesota Zoo": "Minnesota Zoo",
    "Mystic Aquarium": "Mystic Aquarium",
    "National Aquarium": "National Aquarium",
    "Nashville Zoo": "Nashville Zoo",
    "North Carolina Zoo": "North Carolina Zoo",
    "Oglebay Good Zoo": "Oglebay Good Zoo",
    "Oklahoma City Zoo": "Oklahoma City Zoo",
    "Oregon Zoo": "Oregon Zoo",
    "Philadelphia Zoo": "Philadelphia Zoo",
    "Phoenix Zoo": "Phoenix Zoo",
    "Riverbanks Zoo and Garden": "Riverbanks Zoo",
    "Roger Williams Park Zoo": "Roger Williams Park Zoo",
    "Saint Louis Zoo": "Saint Louis Zoo",
    "San Diego Zoo": "San Diego Zoo",
    "Sedgwick County Zoo": "Sedgwick County Zoo",
    "Shark Reef Aquarium": "Shark Reef Aquarium at Mandalay Bay",
    "Smithsonian National Zoo": "National Zoological Park (United States)",
    "The Florida Aquarium": "Florida Aquarium",
    "Utah's Hogle Zoo": "Hogle Zoo",
    "Virginia Aquarium and Marine Science Center": "Virginia Aquarium & Marine Science Center",
    "Woodland Park Zoo": "Woodland Park Zoo",
    "Zoo Atlanta": "Zoo Atlanta",
    "Zoo Boise": "Zoo Boise",
    "Zoo Miami": "Zoo Miami",
}


class Command(BaseCommand):
    help = "Fetch representative zoo image URLs from Wikipedia and save them to Zoo.image_url."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Replace existing zoo image URLs.",
        )
        parser.add_argument(
            "--name",
            type=str,
            help="Fetch an image for one zoo by exact name.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit how many zoos are processed in this run.",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]
        zoo_name = (options.get("name") or "").strip()
        limit = options.get("limit")

        zoos = Zoo.objects.filter(is_active=True)

        if zoo_name:
            zoos = zoos.filter(name=zoo_name)

        if not overwrite:
            zoos = zoos.filter(image_url="")

        zoos = zoos.order_by("name")

        if limit:
            zoos = zoos[:limit]

        total = zoos.count() if hasattr(zoos, "count") else len(zoos)
        updated = 0
        skipped = 0

        if total == 0:
            self.stdout.write(self.style.WARNING("No zoos matched the selected filters."))
            return

        for zoo in zoos:
            wiki_title = ZOO_WIKIPEDIA_TITLES.get(zoo.name, zoo.name)
            wiki_data = fetch_wikipedia_summary(wiki_title)

            if not wiki_data or not wiki_data.get("image_url"):
                self.stdout.write(self.style.WARNING(f"Skipped {zoo.name}: no Wikipedia image found."))
                skipped += 1
                continue

            zoo.image_url = wiki_data["image_url"]
            zoo.save(update_fields=["image_url"])
            updated += 1
            self.stdout.write(self.style.SUCCESS(f"Updated {zoo.name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Zoo image fetch complete. Updated: {updated}. Skipped: {skipped}."
            )
        )
