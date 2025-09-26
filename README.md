# Стимулирующие выплаты ИЦО МГПУ

Веб-приложение на Django для ведения списка сотрудников, управления стимулирующими выплатами и подачи заявок ответственными лицами.

## Архитектура деплоя

Развёртывание разделено на два независимых компонента:

- **Backend (Django API)** — размещается на бесплатном тарифе Render (или другом совместимом PaaS). Занимается аутентификацией, CRUD по сотрудникам и заявкам, хранит данные в PostgreSQL.
- **Frontend (статический)** — размещается на GitHub Pages. Работает как SPA на чистом JavaScript и обращается к API по HTTPS.

Текущий репозиторий содержит оба компонента: `stimul_ico/` (backend) и `frontend/` (статический клиент). CI/CD настроен через GitHub Actions: при каждом пуше в ветку `main` автоматически собирается каталог `frontend/` и публикуется на Pages, подставляя адрес API из переменной окружения.

## Возможности

- Полный список сотрудников ИЦО с полями из Excel-таблицы
- Фильтрация по ФИО, подразделению и категории (АУП/ППС)
- Создание, редактирование и удаление карточек сотрудников (для админов)
- Подача заявок на стимулирование ответственными сотрудниками через статический фронтенд
- Просмотр заявок, смена статуса и добавление комментариев администраторами через API
- Встроенная панель администратора Django
- Импорт сотрудников из файла `Таблица по стимулу 2025-2026 (2).xlsx`

## Требования

- Python 3.11+
- PostgreSQL (для продакшн-развёртывания на Render)
- Node.js не требуется: статический фронтенд написан без сборщиков

## Быстрый старт локально

1. Создать и активировать виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Выполнить миграции БД:
   ```bash
   cd stimul_ico
   python manage.py migrate
   ```

4. Создать суперпользователя (админ-доступ):
   ```bash
   python manage.py createsuperuser
   ```

5. Создать роли и права доступа:
   ```bash
   python manage.py setup_roles
   ```
   - Добавьте созданного суперпользователя в группу «Администраторы» через `python manage.py shell` или через админку.
   - Ответственных добавляйте в группу «Ответственные».

6. Импортировать сотрудников из Excel (используется исходный файл из корня репозитория):
   ```bash
   python manage.py import_employees "../Таблица по стимулу 2025-2026 (2).xlsx"
   ```
   При необходимости можно полностью очистить сотрудников и переимпортировать:
   ```bash
   python manage.py import_employees "../Таблица по стимулу 2025-2026 (2).xlsx" --truncate
   ```

7. Запустить сервер разработки:
   ```bash
   python manage.py runserver
   ```

8. Для локального тестирования фронтенда откройте файл `frontend/index.html` в браузере и укажите `window.STIMUL_API_BASE_URL` (например, через временное редактирование `config.template.js` и генерацию `frontend/config.js`).

## Настройка GitHub Pages

1. Создайте репозиторий на GitHub и загрузите код проекта.
2. В разделе **Settings → Secrets and variables → Actions** добавьте переменную `PAGES_API_BASE_URL` со значением `https://<render-сервис>.onrender.com` (или кастомный домен backend).
3. Убедитесь, что GitHub Pages включён в режиме **Deploy from a branch → GitHub Actions**.
4. После пуша в ветку `main` сработает workflow `.github/workflows/deploy-pages.yml`, который собирает папку `frontend/`, подставляет адрес API и публикует содержимое на Pages.

## Развёртывание backend на Render (Free Plan)

1. Импортируйте репозиторий в Render и выберите **Blueprint (YAML)**.
2. Render автоматически обнаружит файл `render.yaml` и создаст два ресурса:
   - Web Service `stimul-ico-backend` (Python 3.11, бесплатный план)
   - PostgreSQL базу `stimul-ico-db` (также бесплатный план)
3. После создания сервиса выполните настройки:
   - В переменную `DJANGO_ALLOWED_HOSTS` пропишите домен Render (например, `stimul-ico-backend.onrender.com`).
   - В `DJANGO_CORS_ALLOWED_ORIGINS` укажите публичный адрес GitHub Pages (`https://<username>.github.io`).
   - Дополнительно можно добавить переменные `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY=<собственный_секрет>` (если не хотите автогенерацию).
4. Render будет выполнять команды, описанные в `render.yaml`:
   - `pip install -r requirements.txt && python stimul_ico/manage.py collectstatic --noinput`
   - `python stimul_ico/manage.py migrate --noinput`
   - `gunicorn stimul_ico.wsgi:application`
5. После первого деплоя создайте суперпользователя:
   ```bash
   render ssh <service-name>
   python stimul_ico/manage.py createsuperuser
   ```
   или временно включите Render Shell.

## Переменные окружения backend

| Переменная | Назначение |
| ---------- | ---------- |
| `DJANGO_SECRET_KEY` | Секрет Django, автоматически генерируется Render, но можно задать вручную |
| `DJANGO_DEBUG` | `0` для продакшна, `1` для отладки |
| `DJANGO_ALLOWED_HOSTS` | Список доменов, разделённых пробелом (`stimul-ico-backend.onrender.com`) |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Разрешённые источники CORS (например, `https://<username>.github.io`) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | При необходимости добавьте адреса фронтенда для корректной работы форм |
| `DATABASE_URL` | Строка подключения к PostgreSQL, выдаётся Render автоматически |

## API

- Авторизация — POST `/api/auth/token/` (получение токена DRF)
- Профиль текущего пользователя — GET `/api/auth/profile/`
- Сотрудники — GET `/api/employees/`
- Заявки — CRUD `/api/requests/`
- Статусы заявок — GET `/api/requests/statuses/`
- Кампании — GET `/api/campaigns/`

С фронтенда запросы отправляются с заголовком `Authorization: Token <token>`. Для всех API эндпоинтов требуется аутентификация.

## Структура проекта

- `stimul_ico/stimul_ico/` — настройки проекта Django
- `stimul_ico/stimuli/` — приложение с моделями, формами, фильтрами и шаблонами
- `stimul_ico/templates/` — общие шаблоны (включая страницу входа)
- `stimul_ico/static/` — стили интерфейса для серверных шаблонов
- `stimul_ico/api/` — REST API (DRF) для фронтенда на Pages
- `frontend/` — статический фронтенд, развёртываемый на GitHub Pages
- `stimuli/management/commands/` — команды `import_employees` и `setup_roles`

## Примечания

- Все суммы выплат хранятся в формате `Decimal` с точностью до 2 знаков.
- Заявки переходят в статусы: `pending`, `approved`, `rejected`, `archived`.
- Для корректной работы фронтенда необходимо задать переменные окружения и домены CORS на стороне backend.
- При локальной разработке фронтенда удобно запускать Django на `http://127.0.0.1:8000` и определить `window.STIMUL_API_BASE_URL` в `frontend/config.js` вручную.
