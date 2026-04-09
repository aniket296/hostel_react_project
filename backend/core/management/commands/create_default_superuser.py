import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import OperationalError, ProgrammingError


class Command(BaseCommand):
    help = "Create a default superuser when CREATE_SUPERUSER=True and credentials are set."

    def handle(self, *args, **options):
        if os.getenv("CREATE_SUPERUSER", "False") != "True":
            self.stdout.write("CREATE_SUPERUSER is not enabled. Skipping superuser creation.")
            return

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(self.style.WARNING("Superuser credentials missing. Skipping."))
            return

        User = get_user_model()
        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING("Superuser already exists"))
                return
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS("Superuser created successfully"))
        except (OperationalError, ProgrammingError) as exc:
            self.stdout.write(self.style.WARNING(f"Could not create superuser: {exc}"))
