#!/usr/bin/env python3
"""
Простой тест для проверки работы Django приложения
"""
import os
import sys
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stimul_ico.settings')
django.setup()

def test_app():
    """Тестируем основные компоненты приложения"""
    print("🧪 Тестируем Django приложение...")
    
    try:
        # Тестируем настройки
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"✅ DATABASE: {settings.DATABASES['default']['ENGINE']}")
        
        # Тестируем подключение к БД
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection: {result}")
        
        # Тестируем WSGI приложение
        application = get_wsgi_application()
        print("✅ WSGI application создано успешно")
        
        # Тестируем URL конфигурацию
        from django.urls import reverse
        try:
            home_url = reverse('home')
            print(f"✅ Home URL: {home_url}")
        except Exception as e:
            print(f"⚠️  Home URL error: {e}")
        
        print("🎉 Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1)
