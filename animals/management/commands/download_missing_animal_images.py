import mimetypes
import time
from pathlib import Path
from urllib.parse import urlparse, quote

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.text import slugify

from animals.models import Animal


HEADERS = {
    "User-Agent": "SearchWilds/1.0 (animal image downloader; contact: searchwilds.com)",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Referer": "https://en.wikipedia.org/",
}


def get_wikipedia_summary_data(title):
    """
    Try to fetch summary/image/page URL from a known Wikipedia title.
    """
    if not title:
        return "", "", ""

    safe_title = quote(title.replace(" ", "_"))
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}"

    try:
        response = requests.get(api_url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return "", "", ""

        data = response.json()

        summary = data.get("extract", "")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")

        image_url = ""

        if "originalimage" in data:
            image_url = data["originalimage"].get("source", "")
        elif "thumbnail" in data:
            image_url = data["thumbnail"].get("source", "")

        return summary, image_url, page_url

    except requests.RequestException:
        return "", "", ""


def search_wikipedia_title(query):
    """
    Search Wikipedia by animal name and return best matching title.
    """
    if not query:
        return ""

    search_url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1,
    }

    try:
        response = requests.get(
            search_url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True
        )

        if response.status_code != 200:
            return ""

        data = response.json()
        results = data.get("query", {}).get("search", [])

        if not results:
            return ""

        return results[0].get("title", "")

    except requests.RequestException:
        return ""


def get_file_extension(url, response=None):
    path = urlparse(url).path
    ext = Path(path).suffix.lower()

    valid_exts = [".jpg", ".jpeg", ".png", ".webp"]

    if ext in valid_exts:
        return ext

    if response is not None:
        content_type = response.headers.get("Content-Type", "")
        guessed_ext = mimetypes.guess_extension(
            content_type.split(";")[0].strip()
        )

        if guessed_ext in valid_exts:
            return guessed_ext

    return ".jpg"


def download_image_with_retry(image_url, headers, max_retries=3):
    """
    Download image with retry handling for 429 rate limit errors.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(
                image_url,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )

            # Success
            if response.status_code == 200:
                return response

            # Too many requests
            if response.status_code == 429:
                wait_time = 10 * (attempt + 1)
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue

            # Other errors
            return response

        except requests.RequestException:
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                time.sleep(wait_time)
                continue
            raise

    return None

class Command(BaseCommand):
    help = "Download missing animal images into Animal.image"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional limit on number of animals to process"
        )

    def handle(self, *args, **options):
        limit = options.get("limit")

        queryset = Animal.objects.filter(
            Q(image__isnull=True) | Q(image="")
        ).order_by("name")

        if limit:
            queryset = queryset[:limit]

        downloaded = 0
        skipped = 0
        failed = 0

        for animal in queryset:
            self.stdout.write(f"Processing: {animal.name}")

            image_url = animal.wiki_image_url or ""
            summary = animal.wiki_summary or ""
            page_url = animal.wiki_page_url or ""
            wiki_title = animal.wiki_title or ""

            # Step 1: Try current wiki_title
            if not image_url and wiki_title:
                summary, image_url, page_url = get_wikipedia_summary_data(wiki_title)

            # Step 2: If wiki_title failed, search by animal name
            if not image_url:
                searched_title = search_wikipedia_title(animal.name)

                if searched_title:
                    wiki_title = searched_title
                    summary, image_url, page_url = get_wikipedia_summary_data(searched_title)

            # Step 3: Save wiki fields if found
            updated = False

            if wiki_title and animal.wiki_title != wiki_title:
                animal.wiki_title = wiki_title
                updated = True

            if summary and not animal.wiki_summary:
                animal.wiki_summary = summary
                updated = True

            if image_url and animal.wiki_image_url != image_url:
                animal.wiki_image_url = image_url
                updated = True

            if page_url and animal.wiki_page_url != page_url:
                animal.wiki_page_url = page_url
                updated = True

            if updated:
                animal.save()

            if not image_url:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Skipped: no image URL found for {animal.name}"
                    )
                )
                skipped += 1
                continue

            # Step 4: Download image
            try:
                response = download_image_with_retry(image_url, HEADERS)

                if response is None:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Failed: no response for {animal.name}. URL: {image_url}"
                        )
                    )
                    failed += 1
                    continue

                if response.status_code != 200:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Failed: could not download image for {animal.name}. "
                            f"Status code: {response.status_code}. URL: {image_url}"
                        )
                    )
                    failed += 1
                    time.sleep(3)
                    continue

                content_type = response.headers.get("Content-Type", "")

                if not content_type.startswith("image/"):
                    self.stdout.write(
                        self.style.ERROR(
                            f"  Failed: URL is not an image for {animal.name}. "
                            f"Content-Type: {content_type}. URL: {image_url}"
                        )
                    )
                    failed += 1
                    continue

                ext = get_file_extension(image_url, response=response)
                filename = f"{slugify(animal.name)}{ext}"

                animal.image.save(
                    filename,
                    ContentFile(response.content),
                    save=True
                )

                downloaded += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Downloaded image for {animal.name}"
                    )
                )

                time.sleep(3)

            except requests.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"  Error downloading {animal.name}: {e}"
                    )
                )
                failed += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Finished downloading animal images"))
        self.stdout.write(self.style.SUCCESS(f"Downloaded: {downloaded}"))
        self.stdout.write(self.style.WARNING(f"Skipped: {skipped}"))
        self.stdout.write(self.style.ERROR(f"Failed: {failed}"))