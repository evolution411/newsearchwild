from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import EmailMultiAlternatives


class Command(BaseCommand):
    help = "Send a test email using the current Django email settings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            required=True,
            help="Recipient email address"
        )

    def handle(self, *args, **options):
        recipient = options["to"].strip()

        if not recipient:
            raise CommandError("Please provide a recipient with --to")

        subject = "Search Wilds test email"
        text_content = (
            "This is a test email from Search Wilds.\n\n"
            "If you received this message, your Django email settings are working."
        )
        html_content = """
        <html>
          <body style="font-family:Arial,Helvetica,sans-serif;background:#f6f4ec;padding:24px;color:#163022;">
            <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:18px;padding:28px;box-shadow:0 16px 40px rgba(12,32,21,0.12);">
              <h1 style="margin-top:0;color:#174f2d;">Search Wilds test email</h1>
              <p style="line-height:1.7;color:#32463a;">
                If you received this message, your Django email settings are working correctly.
              </p>
            </div>
          </body>
        </html>
        """

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_content, "text/html")
        message.send(fail_silently=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Test email sent to {recipient} using {settings.EMAIL_BACKEND}"
            )
        )
