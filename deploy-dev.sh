#!/bin/bash
set -e

echo "🚀 Начинаем безопасный деплой Stimul ICO..."

# Проверяем, что мы не в продакшн режиме
if [ "$DJANGO_DEBUG" = "0" ]; then
    echo "⚠️  ВНИМАНИЕ: Вы находитесь в продакшн режиме!"
    echo "Этот скрипт предназначен для разработки."
    echo "Для продакшна используйте: docker-compose -f docker-compose.prod.yml up -d"
    exit 1
fi

# Создаем директории для данных если их нет
mkdir -p docker_data

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose down

# Удаляем старые образы (опционально)
echo "🧹 Очищаем старые образы..."
docker image prune -f

# Собираем новый образ
echo "🔨 Собираем новый образ..."
docker-compose build --no-cache

# Запускаем контейнеры
echo "▶️  Запускаем контейнеры..."
docker-compose up -d

# Ждем запуска
echo "⏳ Ждем запуска сервисов..."
sleep 10

# Проверяем статус
echo "📊 Проверяем статус контейнеров..."
docker-compose ps

echo "✅ Деплой завершен!"
echo "🌐 Приложение доступно по адресу: http://localhost:8000"
echo "📝 Логи: docker-compose logs -f"
