# Настройка переменных окружения для Railway

## Обязательные переменные окружения

Установите следующие переменные в настройках сервиса Railway:

### Основные настройки Django
```
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=your-secret-key-here
```

### Настройки Railway
```
RAILWAY_HEALTHCHECK_TIMEOUT_SEC=300
```

### Настройки Gunicorn (опционально)
```
GUNICORN_WORKERS=3
```

## Автоматически устанавливаемые Railway переменные

Railway автоматически устанавливает:
- `PORT` - порт для приложения (обычно 8080)
- `DATABASE_URL` - URL подключения к PostgreSQL
- `RAILWAY_PUBLIC_DOMAIN` - публичный домен сервиса

## Проверка healthcheck

После деплоя проверьте:
1. Логи запуска - должны показать успешный старт Gunicorn
2. Healthcheck endpoint: `https://your-app.railway.app/health/`
3. Должен вернуть статус 200 с информацией о системе

## Troubleshooting

Если healthcheck не проходит:

1. **Проверьте ALLOWED_HOSTS** - должен включать `healthcheck.railway.app`
2. **Проверьте порт** - приложение должно слушать на переменной `PORT`
3. **Проверьте логи** - ищите ошибки в логах Railway
4. **Проверьте базу данных** - убедитесь, что `DATABASE_URL` установлен правильно

## Пример успешного healthcheck ответа

```
OK - Debug: False, DB: Connected, PORT: 8080, Railway: your-app.railway.app
```
