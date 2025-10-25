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
python backend/manage.py collectstatic --noinput --clear

# Проверяем, что статические файлы собраны
if [ ! -d "backend/staticfiles" ]; then
    echo "⚠️  Предупреждение: staticfiles директория не создана"
else
    echo "✅ Статические файлы собраны успешно"
    echo "📁 Размер staticfiles: $(du -sh backend/staticfiles)"
fi

echo "🌐 Запускаем Gunicorn..."
echo "🔍 Проверяем переменные окружения:"
echo "  - PORT: ${PORT:-8000}"
echo "  - GUNICORN_WORKERS: ${GUNICORN_WORKERS:-3}"
echo "  - DATABASE_URL: ${DATABASE_URL:+Set}"
echo "  - DJANGO_DEBUG: ${DJANGO_DEBUG:-Not set}"
echo "  - RAILWAY_PUBLIC_DOMAIN: ${RAILWAY_PUBLIC_DOMAIN:-Not set}"
echo "  - RAILWAY_HEALTHCHECK_TIMEOUT_SEC: ${RAILWAY_HEALTHCHECK_TIMEOUT_SEC:-300}"

# Ensure correct import path for the Django project package under backend/
echo "🚀 Запуск сервера на порту ${PORT:-8000}..."

# Проверяем, что мы в правильной директории
echo "📁 Текущая директория: $(pwd)"
echo "📁 Содержимое директории:"
ls -la

# Проверяем, что backend директория существует
if [ ! -d "backend" ]; then
    echo "❌ ОШИБКА: Директория backend не найдена!"
    exit 1
fi

echo "📁 Содержимое backend директории:"
ls -la backend/

# Проверяем, что manage.py существует
if [ ! -f "backend/manage.py" ]; then
    echo "❌ ОШИБКА: manage.py не найден!"
    exit 1
fi

# Проверяем, что wsgi.py существует
if [ ! -f "backend/stimul_ico/wsgi.py" ]; then
    echo "❌ ОШИБКА: wsgi.py не найден!"
    exit 1
fi

echo "✅ Все файлы найдены, запускаем Gunicorn..."

# Тестируем Django приложение перед запуском
echo "🧪 Тестируем Django приложение..."
python backend/manage.py check --deploy

if [ $? -ne 0 ]; then
    echo "❌ ОШИБКА: Django check failed!"
    exit 1
fi

echo "✅ Django check прошел успешно!"

# Дополнительный тест приложения
echo "🧪 Дополнительный тест приложения..."
python test_app.py

if [ $? -ne 0 ]; then
    echo "❌ ОШИБКА: App test failed!"
    exit 1
fi

echo "✅ App test прошел успешно!"

# Запускаем Gunicorn с подробным логированием
echo "🚀 Запускаем Gunicorn на порту ${PORT:-8000}..."
exec gunicorn --chdir backend stimul_ico.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-3} \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --log-level debug \
    --access-logfile - \
    --error-logfile -
