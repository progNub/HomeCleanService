# Use an official Python runtime based on Debian 12 "bookworm" as a parent image.
FROM python:3.12-slim-bookworm

# Add user that will be used in the container.
RUN useradd -m wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
    curl \
    gnupg \
 && rm -rf /var/lib/apt/lists/*

# Install Node.js (needed for Sass/Bootstrap compilation)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# Install the application server and uv for python dependency management
RUN pip install "gunicorn==20.0.4" uv

# Use /app folder as a directory where the source code is stored.
WORKDIR /app
RUN chown wagtail:wagtail /app

COPY pyproject.toml uv.lock ./
COPY package.json package-lock.json ./

# Install frontend dependencies
RUN npm install
# Install the project requirements.
RUN uv pip install --system --no-cache .

# Set this directory to be owned by the "wagtail" user. This Wagtail project
# uses SQLite, the folder needs to be owned by the user that
# will be writing to the database file.


# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail . .

# Set environment variable for production
ENV DJANGO_SETTINGS_MODULE=settings.production

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Collect static files (Sass will be compiled during this step by django-compressor)

RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput --clear
RUN python manage.py compress --force

# Runtime command that executes when "docker run" is called
ENTRYPOINT ["/app/deploy/scripts/entrypoint.sh"]
