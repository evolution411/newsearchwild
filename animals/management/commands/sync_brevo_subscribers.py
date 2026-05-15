import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from animals.models import NewsletterSubscriber


class Command(BaseCommand):
    help = "Sync active newsletter subscribers to Brevo"

    def handle(self, *args, **options):
        if not settings.BREVO_API_KEY:
            self.stdout.write(self.style.ERROR("Missing BREVO_API_KEY"))
            return

        list_ids = []
        if settings.BREVO_LIST_ID:
            try:
                list_ids = [int(settings.BREVO_LIST_ID)]
            except ValueError:
                self.stdout.write(self.style.ERROR("BREVO_LIST_ID must be a number"))
                return

        synced = 0
        failed = 0

        for subscriber in NewsletterSubscriber.objects.filter(is_active=True):
            payload = {
                "email": subscriber.email,
                "emailBlacklisted": False,
                "updateEnabled": True,
            }

            if list_ids:
                payload["listIds"] = list_ids

            response = requests.post(
                "https://api.brevo.com/v3/contacts",
                headers={
                    "accept": "application/json",
                    "api-key": settings.BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json=payload,
                timeout=20,
            )

            if response.status_code in (200, 201, 204):
                synced += 1
                self.stdout.write(self.style.SUCCESS(f"Synced: {subscriber.email}"))
            else:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed: {subscriber.email} ({response.status_code}) {response.text[:200]}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Brevo sync complete. Synced: {synced}, Failed: {failed}")
        )
