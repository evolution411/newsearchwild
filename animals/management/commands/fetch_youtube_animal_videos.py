import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from animals.models import Animal, AnimalVideo


class Command(BaseCommand):
    help = "Fetch YouTube Shorts animal videos and save them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--animal",
            type=str,
            default=None,
            help="Animal name, for example Tiger"
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Number of videos per animal"
        )

    def handle(self, *args, **options):
        api_key = settings.YOUTUBE_API_KEY

        if not api_key:
            self.stdout.write(self.style.ERROR("Missing YOUTUBE_API_KEY"))
            return

        animal_name = options.get("animal")
        limit = options.get("limit")

        if animal_name:
            animals = Animal.objects.filter(name__iexact=animal_name)
        else:
            animals = Animal.objects.all()

        created_count = 0
        skipped_count = 0

        for animal in animals:
            query = f"{animal.name} animal facts shorts wildlife"

            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "videoDuration": "short",
                "maxResults": limit,
                "key": api_key,
                "safeSearch": "moderate",
            }

            response = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params=params,
                timeout=20
            )

            if response.status_code != 200:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed for {animal.name}: {response.status_code} {response.text[:200]}"
                    )
                )
                continue

            data = response.json()

            for item in data.get("items", []):
                video_id = item.get("id", {}).get("videoId")

                if not video_id:
                    skipped_count += 1
                    continue

                snippet = item.get("snippet", {})
                title = snippet.get("title", "")
                description = snippet.get("description", "")
                thumbnail_url = snippet.get("thumbnails", {}).get("high", {}).get("url", "")

                video_url = f"https://www.youtube.com/shorts/{video_id}"
                embed_url = f"https://www.youtube.com/embed/{video_id}"

                obj, created = AnimalVideo.objects.get_or_create(
                    platform="youtube",
                    video_url=video_url,
                    defaults={
                        "animal": animal,
                        "category": animal.category,
                        "title": title[:200],
                        "description": description,
                        "embed_url": embed_url,
                        "thumbnail_url": thumbnail_url,
                        "is_active": True,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Saved YouTube video for {animal.name}: {title[:60]}"
                        )
                    )
                else:
                    skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, Skipped: {skipped_count}"
            )
        )