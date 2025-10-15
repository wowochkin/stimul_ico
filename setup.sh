#!/bin/bash
set -e

# Применяем миграции
python backend/manage.py migrate

# Создаем суперпользователя (если не существует)
python backend/manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')
    print('Superuser created')
else:
    print('Superuser already exists')
"