#!/bin/sh
set -e

# Проверяем, существует ли база данных
if [ ! -f "backend/db.sqlite3" ]; then
    echo "База данных не найдена, создаем новую..."
    python backend/manage.py migrate --noinput
else
    echo "База данных найдена, применяем только новые миграции..."
    python backend/manage.py migrate --noinput
fi

# Собираем статические файлы
python backend/manage.py collectstatic --noinput

# Ensure correct import path for the Django project package under backend/
gunicorn --chdir backend stimul_ico.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
