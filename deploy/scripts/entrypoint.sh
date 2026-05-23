#!/bin/bash

# Останавливаем скрипт при ошибке
set -e

echo "--> Выполнение миграций..."
python manage.py migrate --noinput
echo "--> Сбор статических файлов..."
python manage.py collectstatic --noinput --clear
python manage.py compress --force
echo "--> Инициализация данных сайта..."
python manage.py init_site

echo "--> Запуск Gunicorn..."
exec gunicorn cms.wsgi:application \
    --name homeservice \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --log-level=info \
    --access-logfile - \
    --error-logfile -
