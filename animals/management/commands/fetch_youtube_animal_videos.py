import time

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

        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="Only fetch videos for animals in this category name"
        )

        parser.add_argument(
            "--offset",
            type=int,
            default=0,
            help="Start from this position in the animal queryset"
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=None,
            help="Limit how many animals are processed in this run"
        )

        parser.add_argument(
            "--skip-with-videos",
            action="store_true",
            help="Skip animals that already have active YouTube videos"
        )

        parser.add_argument(
            "--delay-seconds",
            type=float,
            default=0,
            help="Pause between animals to reduce API bursts"
        )

    def handle(self, *args, **options):
        api_key = settings.YOUTUBE_API_KEY

        if not api_key:
            self.stdout.write(self.style.ERROR("Missing YOUTUBE_API_KEY"))
            return

        animal_name = options.get("animal")
        category_name = options.get("category")
        limit = options.get("limit")
        offset = max(options.get("offset") or 0, 0)
        batch_size = options.get("batch_size")
        skip_with_videos = options.get("skip_with_videos", False)
        delay_seconds = max(options.get("delay_seconds") or 0, 0)

        if animal_name:
            animals = Animal.objects.filter(name__iexact=animal_name)
        else:
            animals = Animal.objects.all()

        if category_name:
            animals = animals.filter(category__name__iexact=category_name)

        if skip_with_videos:
            animals = animals.exclude(videos__platform="youtube", videos__is_active=True)

        animals = animals.select_related("category").distinct().order_by("id")

        if offset:
            animals = animals[offset:]

        if batch_size:
            animals = animals[:batch_size]

        total_animals = animals.count()

        if total_animals == 0:
            self.stdout.write(self.style.WARNING("No animals matched the selected filters."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Fetching YouTube videos for {total_animals} animal(s). "
                f"limit={limit}, offset={offset}, batch_size={batch_size or 'all'}, "
                f"delay_seconds={delay_seconds}"
            )
        )

        created_count = 0
        skipped_count = 0
        processed_count = 0

        for animal in animals:
            processed_count += 1
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

            if delay_seconds and processed_count < total_animals:
                time.sleep(delay_seconds)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Processed animals: {processed_count}, Created videos: {created_count}, Skipped: {skipped_count}"
            )
        )
