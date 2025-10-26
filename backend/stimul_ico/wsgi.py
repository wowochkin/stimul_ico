import os
import sys
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stimul_ico.settings')

# Получаем Django application
application = get_wsgi_application()
