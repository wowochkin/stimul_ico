import os
import sys
import traceback
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stimul_ico.settings')

# Получаем Django application
try:
    _application = get_wsgi_application()
    print("✅ WSGI application loaded successfully", file=sys.stderr, flush=True)
except Exception as e:
    print(f"❌ WSGI application failed to load: {e}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    raise


# Оборачиваем в обработчик ошибок для диагностики
def application(environ, start_response):
    """WSGI application с логированием ошибок"""
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', '')
    
    try:
        print(f"📝 Incoming request: {method} {path}", file=sys.stderr, flush=True)
        response = _application(environ, start_response)
        print(f"✅ Request completed: {method} {path}", file=sys.stderr, flush=True)
        return response
    except Exception as e:
        print(f"❌ Request failed: {method} {path}", file=sys.stderr, flush=True)
        print(f"❌ Error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        
        # Возвращаем 500 ошибку
        status = '500 Internal Server Error'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return [b'Internal Server Error']
