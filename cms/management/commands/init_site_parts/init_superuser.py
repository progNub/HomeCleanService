from django.conf import settings
from django.contrib.auth.models import User


def init_superuser(command):
    username = settings.ENV_SUPERUSER_USERNAME
    email = settings.ENV_SUPERUSER_EMAIL
    password = settings.ENV_SUPERUSER_PASSWORD

    if username and password:
        if not User.objects.filter(username=username).exists():
            command.stdout.write(f"Creating superuser {username}...")
            User.objects.create_superuser(username=username, email=email, password=password)
            command.stdout.write(command.style.SUCCESS(f"Superuser {username} created!"))
        else:
            command.stdout.write(command.style.WARNING(f"Superuser {username} already exists."))
    else:
        command.stdout.write(command.style.WARNING("SUPERUSER_USERNAME or SUPERUSER_PASSWORD not found in .env"))
