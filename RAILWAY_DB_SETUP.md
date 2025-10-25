# Настройка постоянной базы данных на Railway

## Проблема
При каждом деплое на Railway база данных SQLite сбрасывается, потому что:
- Railway пересоздает контейнер при каждом деплое
- SQLite файл хранится внутри контейнера
- Отсутствует постоянное хранилище для файлов

## Решение: PostgreSQL с постоянным хранилищем

### Шаг 1: Создание PostgreSQL базы данных на Railway

1. Зайдите в ваш проект на Railway
2. Нажмите **"+ New"** → **"Database"** → **"PostgreSQL"**
3. Railway автоматически создаст PostgreSQL базу данных
4. Скопируйте строку подключения из переменной `DATABASE_URL`

### Шаг 2: Настройка переменных окружения

В настройках вашего сервиса на Railway добавьте переменные:

```
DATABASE_URL=postgresql://postgres:password@host:port/database
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=your-app.railway.app
DJANGO_CORS_ALLOWED_ORIGINS=https://your-github-username.github.io
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-github-username.github.io
```

### Шаг 3: Обновление настроек Django

В `backend/stimul_ico/settings.py` уже есть поддержка PostgreSQL:

```python
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
```

### Шаг 4: Первый деплой с PostgreSQL

После настройки переменных окружения:

1. Railway автоматически применит миграции при деплое
2. База данных будет постоянной и не будет сбрасываться
3. Все данные сохранятся между деплоями

### Шаг 5: Создание подразделений и должностей

После первого деплоя выполните в Railway Web Console:

```bash
python backend/manage.py create_basic_divisions
```

## Преимущества PostgreSQL на Railway

✅ **Постоянное хранилище** - данные сохраняются между деплоями  
✅ **Автоматические бэкапы** - Railway делает бэкапы БД  
✅ **Масштабируемость** - можно увеличить ресурсы БД  
✅ **Надежность** - управляемая база данных  
✅ **SSL подключение** - безопасное соединение  

## Миграция существующих данных

Если у вас уже есть данные в SQLite:

1. Экспортируйте данные из локальной SQLite БД
2. Создайте фикстуры: `python manage.py dumpdata > data.json`
3. После настройки PostgreSQL импортируйте: `python manage.py loaddata data.json`

## Проверка работы

После настройки проверьте:

1. Зайдите в админку Django
2. Убедитесь, что данные сохраняются
3. Попробуйте загрузить Excel файл с сотрудниками
4. Проверьте, что данные не теряются при перезапуске сервиса

## Troubleshooting

### Если БД все еще сбрасывается:
- Проверьте, что `DATABASE_URL` правильно настроен
- Убедитесь, что PostgreSQL сервис запущен
- Проверьте логи Railway на ошибки подключения

### Если миграции не применяются:
```bash
python backend/manage.py migrate --noinput
```

### Если нужно сбросить БД (только для разработки):
```bash
python backend/manage.py flush --noinput
python backend/manage.py migrate --noinput
python backend/manage.py create_basic_divisions
```
