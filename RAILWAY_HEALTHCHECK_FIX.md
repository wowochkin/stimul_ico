# Исправление проблемы с Healthcheck на Railway

## Проблема
После последних изменений Railway не может пройти healthcheck, хотя приложение запускается успешно.

## Исправления

### 1. Исправлен порт в Dockerfile
- Изменен `EXPOSE 8000` на `EXPOSE 8080` для соответствия Railway

### 2. Обновлены настройки Django (settings.py)
- Добавлена поддержка `RAILWAY_PUBLIC_DOMAIN` для автоматического определения хоста
- Отключен `SECURE_SSL_REDIRECT` (Railway обрабатывает SSL)
- Улучшена конфигурация `ALLOWED_HOSTS`

### 3. Обновлена конфигурация Railway (railway.json)
- Изменен `healthcheckPath` с `/admin/` на `/health/`
- Увеличен `healthcheckTimeout` до 120 секунд
- Используется специальный healthcheck endpoint

### 4. Улучшен entrypoint.sh
- Добавлено логирование переменной `RAILWAY_PUBLIC_DOMAIN`
- Добавлены параметры Gunicorn для лучшей стабильности:
  - `--timeout 120`
  - `--keep-alive 2`
  - `--max-requests 1000`
  - `--max-requests-jitter 100`
- Использован `exec` для правильного завершения процесса

## Healthcheck Endpoint
Используется специальный endpoint `/health/` который:
- Проверяет основные настройки Django
- Возвращает статус 200 с информацией о системе
- Не требует аутентификации

## Переменные окружения для Railway
Убедитесь, что установлены:
- `DJANGO_DEBUG=0` (для production)
- `DATABASE_URL` (автоматически устанавливается Railway)
- `RAILWAY_PUBLIC_DOMAIN` (автоматически устанавливается Railway)

## Проверка деплоя
После деплоя проверьте:
1. Логи запуска - должны показать успешный старт Gunicorn
2. Healthcheck должен проходить на `/health/`
3. Приложение должно быть доступно по публичному URL Railway
