"""
Конфигурация Gunicorn для Stimul ICO на Railway
"""
import os
import multiprocessing

# Привязка к адресу и порту - УБРАНО, будет из командной строки
# bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

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

# Рабочая директория - НЕ ИСПОЛЬЗУЕМ, будет установлена через entrypoint.sh
# chdir = '/app/backend'

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

def on_starting(server):
    """Вызывается перед запуском сервера"""
    try:
        import sys
        import os
        port = os.environ.get('PORT', '8000')
        print(f"🚀 Gunicorn запускается на 0.0.0.0:{port}", file=sys.stderr, flush=True)
        print(f"👷 Количество workers: {workers}", file=sys.stderr, flush=True)
    except:
        pass

def when_ready(server):
    """Вызывается когда сервер готов принимать запросы"""
    try:
        import sys
        print("✅ Gunicorn готов принимать запросы", file=sys.stderr, flush=True)
    except:
        pass

def on_exit(server):
    """Вызывается при остановке сервера"""
    try:
        import sys
        print("👋 Gunicorn завершает работу", file=sys.stderr, flush=True)
    except:
        pass

def post_worker_init(worker):
    """Вызывается после инициализации каждого worker'а"""
    import sys
    try:
        print(f"✅ Worker {worker.pid} инициализирован", file=sys.stderr, flush=True)
    except Exception as e:
        # Даже если что-то пошло не так, не падаем
        pass

def worker_int(worker):
    """Вызывается когда worker получает SIGINT или SIGQUIT"""
    try:
        import sys
        print(f"⚠️  Worker {worker.pid} получил сигнал прерывания", file=sys.stderr, flush=True)
    except:
        pass

def worker_abort(worker):
    """Вызывается когда worker получает SIGABRT"""
    try:
        import sys
        print(f"❌ Worker {worker.pid} аварийно завершен", file=sys.stderr, flush=True)
    except:
        pass
    
def worker_exit(server, worker):
    """Вызывается когда worker выходит"""
    try:
        import sys
        print(f"👋 Worker {worker.pid} завершил работу", file=sys.stderr, flush=True)
    except:
        pass

