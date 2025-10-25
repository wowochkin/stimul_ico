#!/bin/bash
set -e

echo "🚀 Начинаем продакшн деплой Stimul ICO..."

# Проверяем переменные окружения
if [ -z "$DJANGO_SECRET_KEY" ]; then
    echo "❌ ОШИБКА: DJANGO_SECRET_KEY не установлен!"
    exit 1
fi

if [ -z "$DJANGO_ALLOWED_HOSTS" ]; then
    echo "❌ ОШИБКА: DJANGO_ALLOWED_HOSTS не установлен!"
    exit 1
fi

echo "✅ Переменные окружения проверены"

# Создаем директории для данных если их нет
mkdir -p docker_data

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose -f docker-compose.prod.yml down

# Собираем новый образ
echo "🔨 Собираем новый образ для продакшна..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Запускаем контейнеры
echo "▶️  Запускаем продакшн контейнеры..."
docker-compose -f docker-compose.prod.yml up -d

# Ждем запуска
echo "⏳ Ждем запуска сервисов..."
sleep 15

# Проверяем статус
echo "📊 Проверяем статус контейнеров..."
docker-compose -f docker-compose.prod.yml ps

# Проверяем логи на ошибки
echo "📝 Проверяем логи на ошибки..."
if docker-compose -f docker-compose.prod.yml logs | grep -i error; then
    echo "⚠️  Обнаружены ошибки в логах!"
    echo "Проверьте логи: docker-compose -f docker-compose.prod.yml logs"
else
    echo "✅ Ошибок в логах не обнаружено"
fi

echo "✅ Продакшн деплой завершен!"
echo "🌐 Приложение должно быть доступно по настроенному домену"
echo "📝 Логи: docker-compose -f docker-compose.prod.yml logs -f"
echo "🔧 Для инициализации данных выполните команды из DEPLOY_QUICK_START.md"
