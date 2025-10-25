# 🚀 Решение проблемы сброса базы данных на Railway

## 🔍 Проблема
При каждом деплое на Railway база данных SQLite сбрасывается, потому что:
- Railway пересоздает контейнер при каждом деплое
- SQLite файл хранится внутри контейнера
- Отсутствует постоянное хранилище для файлов

## ✅ Решение: PostgreSQL с постоянным хранилищем

### Шаг 1: Создание PostgreSQL базы данных на Railway

1. **Зайдите в ваш проект на Railway**
2. **Нажмите "+ New" → "Database" → "PostgreSQL"**
3. **Railway автоматически создаст PostgreSQL базу данных**
4. **Скопируйте строку подключения из переменной `DATABASE_URL`**

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

### Шаг 3: Первый деплой с PostgreSQL

После настройки переменных окружения Railway автоматически:
- Применит миграции при деплое
- Создаст постоянную базу данных
- Сохранит все данные между деплоями

### Шаг 4: Создание подразделений и должностей

После первого деплоя выполните в Railway Web Console:

```bash
python backend/manage.py create_basic_divisions
```

## 📦 Миграция существующих данных

Если у вас уже есть данные в локальной SQLite БД:

### Экспорт данных:
```bash
# Экспорт всех данных
python manage.py export_data

# Экспорт только подразделений и должностей
python manage.py export_data --app staffing --app stimuli
```

### Импорт данных на Railway:
```bash
# После настройки PostgreSQL на Railway
python backend/manage.py import_data fixtures/staffing_data.json
python backend/manage.py import_data fixtures/stimuli_data.json
```

## 🛠️ Созданные инструменты

### 1. Команда `create_basic_divisions`
Быстро создает основные подразделения и должности:
```bash
python manage.py create_basic_divisions
```

### 2. Команда `create_divisions_from_excel`
Создает подразделения и должности из Excel файла:
```bash
python manage.py create_divisions_from_excel /path/to/file.xlsx
```

### 3. Команда `export_data`
Экспортирует данные в фикстуры:
```bash
python manage.py export_data --app staffing --app stimuli
```

### 4. Команда `import_data`
Импортирует данные из фикстур:
```bash
python manage.py import_data fixtures/data.json
```

### 5. Автоматическое создание при загрузке Excel
Теперь при загрузке Excel файла система автоматически создает недостающие подразделения и должности.

## 🎯 Преимущества PostgreSQL на Railway

✅ **Постоянное хранилище** - данные сохраняются между деплоями  
✅ **Автоматические бэкапы** - Railway делает бэкапы БД  
✅ **Масштабируемость** - можно увеличить ресурсы БД  
✅ **Надежность** - управляемая база данных  
✅ **SSL подключение** - безопасное соединение  
✅ **Не нужно перезаписывать БД** при обновлении репозитория  

## 🔧 Проверка работы

После настройки PostgreSQL проверьте:

1. **Зайдите в админку Django**
2. **Убедитесь, что данные сохраняются**
3. **Попробуйте загрузить Excel файл с сотрудниками**
4. **Проверьте, что данные не теряются при перезапуске сервиса**

## 🚨 Troubleshooting

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

## 📋 Итоговый план действий

1. **Создайте PostgreSQL базу данных на Railway**
2. **Настройте переменную `DATABASE_URL`**
3. **Деплойте приложение** - миграции применятся автоматически
4. **Выполните `create_basic_divisions`** для создания подразделений
5. **Загрузите Excel файл с сотрудниками** - система автоматически создаст недостающие записи

Теперь ваша база данных будет постоянной и не будет сбрасываться при каждом деплое! 🎉
