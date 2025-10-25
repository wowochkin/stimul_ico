#!/bin/sh
set -e

echo "🚀 Запуск Stimul ICO..."

# Проверяем переменные окружения
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL не установлен, используем SQLite"
else
    echo "✅ DATABASE_URL установлен, используем PostgreSQL"
fi

# Проверяем, существует ли база данных (только для SQLite)
if [ -z "$DATABASE_URL" ] && [ ! -f "backend/db.sqlite3" ]; then
    echo "📁 База данных SQLite не найдена, создаем новую..."
    python backend/manage.py migrate --noinput
else
    echo "📁 Применяем миграции..."
    python backend/manage.py migrate --noinput
fi

# Собираем статические файлы
echo "📦 Собираем статические файлы..."
python backend/manage.py collectstatic --noinput

echo "🌐 Запускаем Gunicorn..."
echo "🔍 Проверяем переменные окружения:"
echo "  - PORT: ${PORT:-8000}"
echo "  - GUNICORN_WORKERS: ${GUNICORN_WORKERS:-3}"
echo "  - DATABASE_URL: ${DATABASE_URL:+Set}"
echo "  - DJANGO_DEBUG: ${DJANGO_DEBUG:-Not set}"

# Ensure correct import path for the Django project package under backend/
gunicorn --chdir backend stimul_ico.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-3}
