# Команды для применения миграций в Railway

## Вариант 1: Через Railway CLI (рекомендуется)

```bash
# 1. Установите Railway CLI (если еще не установлен)
npm i -g @railway/cli

# 2. Войдите в Railway
railway login

# 3. Подключитесь к вашему проекту
railway link

# 4. Примените миграции
railway run python manage.py migrate

# Или для конкретного приложения
railway run python manage.py migrate stimuli
```

## Вариант 2: Через Git Push (если настроен авто-деплой)

```bash
# 1. Добавьте изменения в git
git add backend/stimuli/migrations/0010_add_can_view_all_to_userdivision.py
git add backend/stimuli/models.py
git add backend/stimuli/admin.py
git add backend/stimuli/permissions.py

# 2. Закоммитьте
git commit -m "Add can_view_all option to UserDivision"

# 3. Отправьте в репозиторий
git push origin main

# Миграции применятся автоматически при деплое
```

## Вариант 3: Через Railway Dashboard

1. Откройте ваш проект в Railway Dashboard
2. Выберите сервис (backend)
3. Перейдите в раздел "Deployments"
4. Найдите последний деплой или создайте новый
5. В разделе "Settings" → "Deploy" добавьте команду:
   ```
   python manage.py migrate
   ```

## Вариант 4: Через SSH/Shell в Railway

1. Откройте Railway Dashboard
2. Выберите сервис (backend)
3. Перейдите в раздел "Deployments"
4. Откройте последний deployment
5. Нажмите на "Open Shell"
6. Выполните команды:
   ```bash
   cd /app
   python manage.py migrate
   ```

## Проверка статуса миграций

```bash
railway run python manage.py showmigrations
```

