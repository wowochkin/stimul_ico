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

echo "🌐 Запускаем Django development server..."
echo "🔍 Проверяем переменные окружения:"
echo "  - PORT: ${PORT:-8000}"
echo "  - DATABASE_URL: ${DATABASE_URL:+Set}"
echo "  - DJANGO_DEBUG: ${DJANGO_DEBUG:-Not set}"
echo "  - RAILWAY_PUBLIC_DOMAIN: ${RAILWAY_PUBLIC_DOMAIN:-Not set}"

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

echo "✅ Все файлы найдены, готовимся к запуску..."

# Простая проверка Django
echo "🧪 Проверяем Django..."
python backend/manage.py check --deploy

if [ $? -ne 0 ]; then
    echo "❌ ОШИБКА: Django check failed!"
    exit 1
fi

echo "✅ Django готов к запуску!"

# Запускаем Gunicorn для Railway
echo "🚀 Запускаем Gunicorn на порту ${PORT:-8000}..."
echo "📡 Сервер будет слушать: 0.0.0.0:${PORT:-8000}"

# Переходим в backend директорию для правильного импорта
cd /app/backend

# Проверяем, что мы в правильной директории
echo "📁 Текущая директория: $(pwd)"
echo "📁 Содержимое директории:"
ls -la

# Проверяем, что wsgi.py существует
if [ ! -f "stimul_ico/wsgi.py" ]; then
    echo "❌ ОШИБКА: wsgi.py не найден в $(pwd)!"
    exit 1
fi

echo "✅ wsgi.py найден, запускаем Gunicorn..."

# Запускаем Gunicorn с конфигом
exec gunicorn --config /app/gunicorn.conf.py stimul_ico.wsgi:application
