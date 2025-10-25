"""
Конфигурация Gunicorn для Stimul ICO на Railway
"""
import os
import multiprocessing

# Привязка к адресу и порту
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Количество worker процессов
workers = int(os.environ.get('GUNICORN_WORKERS', '3'))

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
preload_app = False

# Proxy headers
forwarded_allow_ips = '*'
proxy_protocol = False
proxy_allow_ips = '*'

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
    print(f"✅ Worker {worker.pid} инициализирован")

def worker_int(worker):
    """Вызывается когда worker получает SIGINT или SIGQUIT"""
    print(f"⚠️  Worker {worker.pid} получил сигнал прерывания")

def worker_abort(worker):
    """Вызывается когда worker получает SIGABRT"""
    print(f"❌ Worker {worker.pid} аварийно завершен")

