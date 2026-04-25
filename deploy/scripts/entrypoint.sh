#!/bin/bash

# Останавливаем скрипт при ошибке
set -e

echo "--> Выполнение миграций..."

echo "--> Сбор статических файлов..."

echo "--> Инициализация данных сайта..."
# Мы используем --noinput если команда его поддерживает,
# но наша кастомная команда init_site берет данные из .env
python manage.py init_site

echo "--> Запуск Gunicorn..."
exec gunicorn cms.wsgi:application \
    --name homeservice \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --log-level=info \
    --access-logfile - \
    --error-logfile -
