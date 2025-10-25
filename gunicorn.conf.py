"""
Конфигурация Gunicorn для Stimul ICO на Railway
"""
import os
import multiprocessing

# Привязка к адресу и порту
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Количество worker процессов  
# Временно используем 1 для диагностики
workers = int(os.environ.get('GUNICORN_WORKERS', '1'))

# Тип worker'ов
worker_class = 'sync'

# Максимальное количество одновременных клиентов
worker_connections = 1000

# Таймаут для worker'ов (в секундах)
timeout = 30  # Уменьшаем для быстрой диагностики

# Graceful timeout
graceful_timeout = 10

# Keep-alive соединения
keepalive = 2

# Автоматический перезапуск worker'ов после обработки N запросов
max_requests = 1000
max_requests_jitter = 100

# Рабочая директория
chdir = '/app/backend'

# Логирование
accesslog = '-'  # stdout
errorlog = '-'   # stderr
loglevel = 'debug'  # временно включаем debug для диагностики

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Preload app for better memory usage
# ВАЖНО: False чтобы каждый worker загружал Django независимо
preload_app = False

# Proxy headers - разрешаем все для Railway
forwarded_allow_ips = '*'
proxy_protocol = False
proxy_allow_ips = '*'

# Отключаем daemon mode явно
daemon = False

# Bind к интерфейсу
raw_env = []

# Security headers для работы за Railway proxy
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Отключаем daemon mode
daemon = False

def on_starting(server):
    """Вызывается перед запуском сервера"""
    print(f"🚀 Gunicorn запускается на {bind}")
    print(f"👷 Количество workers: {workers}")

def when_ready(server):
    """Вызывается когда сервер готов принимать запросы"""
    print("✅ Gunicorn готов принимать запросы")

def on_exit(server):
    """Вызывается при остановке сервера"""
    print("👋 Gunicorn завершает работу")

def post_worker_init(worker):
    """Вызывается после инициализации каждого worker'а"""
    import sys
    print(f"✅ Worker {worker.pid} инициализирован", file=sys.stderr, flush=True)
    try:
        # Пробуем импортировать Django, чтобы проверить что всё ОК
        import django
        from django.conf import settings
        print(f"✅ Worker {worker.pid}: Django {django.get_version()} загружен", file=sys.stderr, flush=True)
        print(f"✅ Worker {worker.pid}: DEBUG={settings.DEBUG}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"❌ Worker {worker.pid}: Ошибка загрузки Django: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)

def worker_int(worker):
    """Вызывается когда worker получает SIGINT или SIGQUIT"""
    import sys
    print(f"⚠️  Worker {worker.pid} получил сигнал прерывания", file=sys.stderr, flush=True)

def worker_abort(worker):
    """Вызывается когда worker получает SIGABRT"""
    import sys
    print(f"❌ Worker {worker.pid} аварийно завершен", file=sys.stderr, flush=True)
    
def worker_exit(server, worker):
    """Вызывается когда worker выходит"""
    import sys
    print(f"👋 Worker {worker.pid} завершил работу", file=sys.stderr, flush=True)

