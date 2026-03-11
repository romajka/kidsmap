from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Send a test email using current Django EMAIL_* settings."

    def add_arguments(self, parser):
        parser.add_argument("recipient", help="Recipient email address")
        parser.add_argument(
            "--subject",
            default="KidsMap SMTP test",
            help="Email subject",
        )
        parser.add_argument(
            "--body",
            default="SMTP settings are working.",
            help="Email body",
        )

    def handle(self, *args, **options):
        recipient = (options["recipient"] or "").strip()
        if "@" not in recipient:
            raise CommandError("Recipient must be a valid email address.")

        from_email = settings.DEFAULT_FROM_EMAIL
        if not from_email:
            raise CommandError("DEFAULT_FROM_EMAIL is empty. Set it in environment.")

        connection = get_connection()
        try:
            connection.open()
        except Exception as exc:
            raise CommandError(f"SMTP connection failed: {exc}") from exc

        message = EmailMessage(
            subject=options["subject"],
            body=options["body"],
            from_email=from_email,
            to=[recipient],
            connection=connection,
        )

        try:
            sent = message.send(fail_silently=False)
        except Exception as exc:
            raise CommandError(f"Email send failed: {exc}") from exc
        finally:
            connection.close()

        if sent != 1:
            raise CommandError("Email was not sent (SMTP returned 0).")

        self.stdout.write(self.style.SUCCESS(f"Test email sent to {recipient}"))
