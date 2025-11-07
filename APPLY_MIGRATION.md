# Применение миграции через Railway

## Способ 1: Через Railway CLI (самый простой)

### Шаг 1: Установите Railway CLI (если еще не установлен)

```bash
npm i -g @railway/cli
```

Или через Homebrew (macOS):
```bash
brew install railway
```

### Шаг 2: Войдите в Railway

```bash
railway login
```

Откроется браузер для авторизации.

### Шаг 3: Подключитесь к проекту

```bash
cd /Users/vladimirabramov/Stimul_ICO
railway link
```

Выберите ваш проект из списка.

### Шаг 4: Примените миграцию

```bash
railway run python manage.py migrate stimuli
```

Или примените все миграции:
```bash
railway run python manage.py migrate
```

### Шаг 5: Проверьте статус миграций

```bash
railway run python manage.py showmigrations stimuli
```

---

## Способ 2: Через Railway Dashboard (без CLI)

### Шаг 1: Откройте Railway Dashboard
1. Перейдите на https://railway.app
2. Войдите в свой аккаунт
3. Выберите проект

### Шаг 2: Откройте Shell
1. Выберите сервис (backend)
2. Перейдите в раздел **"Deployments"**
3. Найдите последний deployment (или создайте новый)
4. Нажмите на кнопку **"Open Shell"** или **"Shell"**

### Шаг 3: Выполните команды миграции

```bash
cd /app/backend
python manage.py migrate stimuli
```

Или примените все миграции:
```bash
python manage.py migrate
```

### Шаг 4: Проверьте статус

```bash
python manage.py showmigrations stimuli
```

---

## Способ 3: Через SSH (если настроен)

Если у вас настроен SSH доступ к Railway:

```bash
# Подключитесь через SSH
ssh railway@your-instance.railway.app

# Перейдите в директорию проекта
cd /app/backend

# Примените миграцию
python manage.py migrate stimuli
```

---

## Важно!

⚠️ **Перед применением миграции убедитесь, что:**
1. Файл миграции `0011_add_can_view_own_requests_to_userdivision.py` добавлен в git
2. Изменения закоммичены и запушены в репозиторий (если используете авто-деплой)
3. Сделана резервная копия базы данных (на всякий случай)

---

## Проверка после применения миграции

После применения миграции проверьте:

1. **Статус миграций:**
   ```bash
   railway run python manage.py showmigrations stimuli
   ```
   Должна быть галочка ✅ рядом с `0011_add_can_view_own_requests_to_userdivision`

2. **Проверка в админке:**
   - Откройте админку Railway
   - Перейдите в "Подразделения пользователей" (UserDivision)
   - Убедитесь, что появилась колонка "Может видеть заявки на себя"

3. **Проверка в базе данных (опционально):**
   ```bash
   railway run python manage.py dbshell
   ```
   Затем выполните SQL:
   ```sql
   \d stimuli_userdivision
   ```
   Должно быть поле `can_view_own_requests`

---

## Если что-то пошло не так

### Откат миграции:
```bash
railway run python manage.py migrate stimuli 0010_add_can_view_all_to_userdivision
```

### Просмотр SQL, который будет выполнен:
```bash
railway run python manage.py sqlmigrate stimuli 0011_add_can_view_own_requests_to_userdivision
```

