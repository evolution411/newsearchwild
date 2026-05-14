from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Batch load animal data JSON files and optionally fetch YouTube videos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-imports",
            action="store_true",
            help="Skip JSON imports and only run the video loader"
        )
        parser.add_argument(
            "--skip-videos",
            action="store_true",
            help="Skip YouTube video fetching"
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Number of YouTube videos to fetch per animal"
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
            help="Start from this animal position when fetching videos"
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=None,
            help="How many animals to process in this run when fetching videos"
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
            help="Pause between animals while fetching YouTube videos"
        )

    def handle(self, *args, **options):
        skip_imports = options["skip_imports"]
        skip_videos = options["skip_videos"]

        if not skip_imports:
            self.stdout.write(self.style.SUCCESS("Importing base animal records..."))
            call_command("import_animals")

            self.stdout.write(self.style.SUCCESS("Importing extra animal info..."))
            call_command("import_animal_extra_info")

            self.stdout.write(self.style.SUCCESS("Importing animal locations..."))
            call_command("import_animal_locations")

        if not skip_videos:
            self.stdout.write(self.style.SUCCESS("Fetching YouTube animal videos..."))
            call_command(
                "fetch_youtube_animal_videos",
                limit=options["limit"],
                category=options["category"],
                offset=options["offset"],
                batch_size=options["batch_size"],
                skip_with_videos=options["skip_with_videos"],
                delay_seconds=options["delay_seconds"],
            )

        self.stdout.write(self.style.SUCCESS("Animal content load complete."))
