import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from animals.models import NewsletterSubscriber


class Command(BaseCommand):
    help = "Sync inactive local newsletter subscribers to Brevo email blacklist"

    def handle(self, *args, **options):
        if not settings.BREVO_API_KEY:
            self.stdout.write(self.style.ERROR("Missing BREVO_API_KEY"))
            return

        synced = 0
        failed = 0

        for subscriber in NewsletterSubscriber.objects.filter(is_active=False):
            response = requests.put(
                f"https://api.brevo.com/v3/contacts/{subscriber.email}",
                headers={
                    "accept": "application/json",
                    "api-key": settings.BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json={"emailBlacklisted": True},
                timeout=20,
            )

            if response.status_code in (200, 204):
                synced += 1
                self.stdout.write(self.style.SUCCESS(f"Blacklisted in Brevo: {subscriber.email}"))
            else:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed: {subscriber.email} ({response.status_code}) {response.text[:200]}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Brevo unsubscribe sync complete. Synced: {synced}, Failed: {failed}")
        )
