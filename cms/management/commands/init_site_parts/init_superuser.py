import os
from django.contrib.auth.models import User


def init_superuser(command):
    username = os.getenv("SUPERUSER_USERNAME")
    email = os.getenv("SUPERUSER_EMAIL")
    password = os.getenv("SUPERUSER_PASSWORD")

    if username and password:
        if not User.objects.filter(username=username).exists():
            command.stdout.write(f"Creating superuser {username}...")
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            command.stdout.write(
                command.style.SUCCESS(f"Superuser {username} created!")
            )
        else:
            command.stdout.write(
                command.style.WARNING(f"Superuser {username} already exists.")
            )
    else:
        command.stdout.write(
            command.style.WARNING(
                "SUPERUSER_USERNAME or SUPERUSER_PASSWORD not found in .env"
            )
        )
