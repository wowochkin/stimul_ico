# Исправление "connection refused" ошибки

## 🔍 Диагностика проблемы

Railway возвращал ошибку:
```json
"error":"connection refused"
"upstreamErrors": [
  {"error":"connection refused","duration":95},
  {"error":"connection refused","duration":92},
  {"error":"connection refused","duration":92}
]
```

Это означает, что Railway **НЕ МОЖЕТ ПОДКЛЮЧИТЬСЯ** к контейнеру вообще!

При этом:
- ✅ Gunicorn запускается: `Listening at: http://0.0.0.0:8080`
- ✅ Healthcheck работает: `GET /health/ HTTP/1.1" 200 90`
- ❌ Внешние запросы получают "connection refused"

## 🛠 Что было исправлено

### 1. Упрощен WSGI (`backend/stimul_ico/wsgi.py`)
**Было**: Сложный wrapper с try-except который мог ломать соединения
**Стало**: Простой стандартный WSGI без оберток

### 2. Уменьшено количество workers
**Было**: 3 worker'а
**Стало**: 1 worker для диагностики

Это исключит проблемы с:
- Fork процессов
- Межпроцессным взаимодействием
- Конкуренцией за ресурсы

### 3. Детальная диагностика worker'ов
Добавлены callbacks в `gunicorn.conf.py`:
- `post_worker_init` - проверяет загрузку Django в каждом worker
- `worker_exit` - логирует завершение worker'ов
- Вывод PID и версии Django

### 4. Расширены ALLOWED_HOSTS
Добавлены все варианты Railway доменов:
```python
ALLOWED_HOSTS = [
    RAILWAY_PUBLIC_DOMAIN,
    '.railway.app',      # Все поддомены
    '.up.railway.app',   # Новые домены
    'healthcheck.railway.app',
    # ...
]
```

### 5. Исправлены CSRF_TRUSTED_ORIGINS
```python
CSRF_TRUSTED_ORIGINS = [
    f'https://{RAILWAY_PUBLIC_DOMAIN}',
    'https://*.railway.app',
    'https://*.up.railway.app',
]
```

### 6. CORS разрешен для Railway
```python
if RAILWAY_PUBLIC_DOMAIN:
    CORS_ALLOW_ALL_ORIGINS = True
```

## 📋 Что проверить после деплоя

### 1. Логи запуска worker'а

Должны появиться новые сообщения:
```
✅ Worker 10 инициализирован
✅ Worker 10: Django 4.x загружен
✅ Worker 10: DEBUG=False
✅ WSGI application loaded successfully
✅ PID: 10
```

Если нет этих сообщений - worker падает при инициализации Django!

### 2. Попробуйте endpoints

```bash
# Самый простой
curl https://stimulico-production.up.railway.app/ultra-simple/

# Healthcheck
curl https://stimulico-production.up.railway.app/health/

# Главная
curl https://stimulico-production.up.railway.app/
```

### 3. Проверьте логи на ошибки

Ищите строки с:
- `❌ Worker X: Ошибка загрузки Django:`
- `❌ Worker X аварийно завершен`
- `👋 Worker X завершил работу` (без явной причины)

## 🎯 Возможные причины "connection refused"

### 1. Worker падает при инициализации Django
**Симптом**: Нет сообщений "Worker инициализирован"
**Решение**: Смотреть traceback в логах

### 2. Worker падает на первом запросе
**Симптом**: Worker инициализируется, но запрос не обрабатывается
**Решение**: Смотреть логи Django request handler

### 3. Проблемы с памятью
**Симптом**: Worker убивается системой (OOM killer)
**Решение**: Увеличить лимит памяти в Railway

### 4. Database connection timeout
**Симптом**: Worker зависает на подключении к БД
**Решение**: Проверить DATABASE_URL и доступность PostgreSQL

### 5. Port binding issue
**Симптом**: Gunicorn не может забиндиться на 0.0.0.0:8080
**Решение**: Проверить PORT переменную и права

## 🔧 Если проблема сохраняется

### Вариант 1: Попробовать preload_app = True
В `gunicorn.conf.py`:
```python
preload_app = True  # Загрузить Django ДО форка worker'ов
```

### Вариант 2: Использовать gevent worker
```python
worker_class = 'gevent'  # Асинхронный worker
```

Требует: `pip install gevent`

### Вариант 3: Временно отключить middleware
В `settings.py` закомментировать по одному:
- WhiteNoiseMiddleware
- CorsMiddleware  
- CsrfViewMiddleware

### Вариант 4: Запустить локально с такой же конфигурацией
```bash
export PORT=8080
export DATABASE_URL="postgresql://..."
export RAILWAY_PUBLIC_DOMAIN="localhost"
gunicorn --config gunicorn.conf.py stimul_ico.wsgi:application
```

## 📊 Ожидаемый результат

После этого деплоя:
1. Worker запустится успешно с детальными логами
2. Django загрузится без ошибок
3. Запросы будут обрабатываться
4. Или мы увидим ТОЧНУЮ ошибку в логах

В любом случае, с такой диагностикой причина станет ясна!

