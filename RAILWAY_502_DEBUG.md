# Расширенная диагностика ошибки 502

## Что добавлено для диагностики

### 1. Подробное логирование в WSGI (`backend/stimul_ico/wsgi.py`)
- Логирование всех входящих запросов
- Перехват и логирование всех исключений
- Вывод полного traceback при ошибках

### 2. DEBUG логирование в Django (`backend/stimul_ico/settings.py`)
- Включен уровень DEBUG для всех Django логгеров
- Добавлен логгер для gunicorn.error
- Детальное логирование запросов

### 3. DEBUG логирование в Gunicorn (`gunicorn.conf.py`)
- Изменен loglevel на 'debug'
- Уменьшен timeout с 120 до 30 секунд для быстрой диагностики

### 4. Тестовые endpoints

#### `/ultra-simple/`
Максимально простой endpoint без использования шаблонов, БД, аутентификации.
Просто возвращает текст "OK - Ultra simple test!".

#### `/health/`
Существующий healthcheck с проверкой БД.

#### `/test/`
Существующий тестовый endpoint.

## Что проверить после деплоя

### 1. Проверьте логи на наличие сообщений от WSGI

Должны появиться строки вида:
```
✅ WSGI application loaded successfully
📝 Incoming request: GET /
✅ Request completed: GET /
```

Или при ошибке:
```
📝 Incoming request: GET /
❌ Request failed: GET /
❌ Error: SomeError: details
Traceback...
```

### 2. Попробуйте разные endpoints

Проверьте в браузере или через curl:

```bash
# Самый простой
curl https://stimulico-production.up.railway.app/ultra-simple/

# Healthcheck
curl https://stimulico-production.up.railway.app/health/

# Главная
curl https://stimulico-production.up.railway.app/

# Админка
curl https://stimulico-production.up.railway.app/admin/
```

### 3. Анализ результатов

#### Если `/ultra-simple/` работает, а `/` не работает
Проблема в:
- Middleware (CSRF, Session, WhiteNoise, etc.)
- URL routing в stimuli app
- Views в stimuli app

#### Если все endpoints возвращают 502
Проблема в:
- Gunicorn конфигурации
- WSGI приложении
- Railway proxy настройках
- Переменных окружения

#### Если в логах видны трейсбеки
Проблема ясна из stacktrace.

#### Если в логах вообще нет запросов
Проблема в:
- Railway proxy не может достучаться до контейнера
- Gunicorn упал или не запустился
- Порт 8080 не открыт или не слушается

## Возможные причины 502

### 1. Worker timeout
Запрос занимает больше 30 секунд (теперь), worker убивается Gunicorn'ом.
**Решение**: Увеличить timeout или оптимизировать код.

### 2. Worker crash
Worker падает при обработке запроса (exception не перехвачен).
**Решение**: Смотреть traceback в логах.

### 3. Database connection
Проблемы с подключением к PostgreSQL или долгие запросы.
**Решение**: Проверить DATABASE_URL и conn_max_age.

### 4. Memory limit
Worker убивается из-за нехватки памяти.
**Решение**: Уменьшить количество worker'ов или увеличить лимит памяти.

### 5. Middleware проблемы
Какой-то middleware падает или блокирует запросы.
**Решение**: Временно отключать middleware по одному.

### 6. Static files
WhiteNoise не может найти или обработать статические файлы.
**Решение**: Проверить STATIC_ROOT и collectstatic.

## Следующие шаги

1. **Деплой изменений** - Railway автоматически пересоберет
2. **Проверить логи** - искать сообщения от WSGI wrapper
3. **Тестировать endpoints** - начиная с `/ultra-simple/`
4. **Анализировать traceback** - если есть ошибки

После получения логов с новой диагностикой будет понятно, где именно проблема.

