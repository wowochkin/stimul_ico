# Стимулирующие выплаты ИЦО МГПУ

Веб-приложение на Django для ведения списка сотрудников, управления стимулирующими выплатами и подачи заявок ответственными лицами.

## Архитектура деплоя

Развёртывание разделено на два независимых компонента:

- **Backend (Django API)** — запускается на Koyeb (free tier) из Docker-образа. Использует PostgreSQL, размещённую на бесплатном сервисе Neon (или другом совместимом провайдере).
- **Frontend (статический)** — развёрнут на GitHub Pages. Работает как SPA на чистом JavaScript и обращается к API по HTTPS.

В репозитории присутствуют оба компонента: `stimul_ico/` (backend) и `frontend/` (статический клиент). GitHub Actions автоматически публикует фронтенд на Pages и подставляет адрес API из переменной окружения.

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
- PostgreSQL (Neon, Railway, ElephantSQL и т.п.)
- Node.js не требуется: фронтенд написан без сборщиков

## Быстрый старт локально

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Выполните миграции БД:
   ```bash
   cd backend
   python manage.py migrate
   ```

4. Создайте суперпользователя (админ-доступ):
   ```bash
   python manage.py createsuperuser
   ```

5. Настройте роли и права доступа:
   ```bash
   python manage.py setup_roles
   ```
   - Добавьте суперпользователя в группу «Администраторы» через `python manage.py shell` или через админку.
   - Ответственных сотрудников добавляйте в группу «Ответственные».

6. Импортируйте сотрудников из Excel (файл лежит в корне репозитория):
   ```bash
   python manage.py import_employees "../Таблица по стимулу 2025-2026 (2).xlsx"
   ```
   Для полного переимпорта:
   ```bash
   python manage.py import_employees "../Таблица по стимулу 2025-2026 (2).xlsx" --truncate
   ```

7. Запустите сервер разработки:
   ```bash
   python manage.py runserver
   ```

8. Для локального тестирования фронтенда создайте `frontend/config.js` на основе `config.template.js` и укажите `http://127.0.0.1:8000`.

## GitHub Pages

1. Создайте репозиторий на GitHub и запушьте код.
2. В **Settings → Secrets and variables → Actions** добавьте переменную `PAGES_API_BASE_URL` со значением `https://<koyeb-app>.koyeb.app` (фактический домен API).
3. Включите GitHub Pages с режимом **Build and deployment → GitHub Actions**.
4. После каждого пуша в `main` workflow `.github/workflows/deploy-pages.yml` публикует `frontend/` и подставляет адрес API.

## Развёртывание backend на Koyeb (free tier)

1. Создайте аккаунт на [Koyeb](https://www.koyeb.com/) и [Neon](https://neon.tech/) (или другом бесплатном PostgreSQL-провайдере).
2. На стороне Neon создайте БД и сохраните строку подключения вида `postgres://USER:PASSWORD@HOST/DB`.
3. Форкните/подключите GitHub-репозиторий в Koyeb → **Create Service → GitHub → Use repo**.
4. Koyeb обнаружит `koyeb.yaml` и предложит создать сервис. Укажите переменные окружения:
   - `DJANGO_SECRET_KEY` — собственный секрет
   - `DJANGO_ALLOWED_HOSTS` — `.koyeb.app` (или список доменов, включая кастомные)
   - `DJANGO_CORS_ALLOWED_ORIGINS` — `https://<username>.github.io`
   - `DJANGO_CSRF_TRUSTED_ORIGINS` — `https://<username>.github.io`
   - `DATABASE_URL` — строка подключения Neon
   - при необходимости `DJANGO_DEBUG=0`
5. После первого деплоя откройте **Web Console → shell** и создайте суперпользователя:
   ```bash
   python backend/manage.py createsuperuser
   ```
6. При необходимости загрузите сотрудников:
   ```bash
   python backend/manage.py import_employees "Таблица по стимулу 2025-2026 (2).xlsx"
   ```

Контейнер собирается на базе `Dockerfile`, запуск осуществляется через `entrypoint.sh`, который автоматически выполняет `migrate` и `collectstatic`, затем стартует `gunicorn` на порту 8000.

## Файлы развёртывания

- `Dockerfile` — образ для Koyeb (или любого другого Docker-совместимого PaaS)
- `entrypoint.sh` — скрипт, выполняющий миграции и запускающий `gunicorn`
- `.dockerignore` — исключения при сборке образа
- `koyeb.yaml` — декларативное описание сервиса под Koyeb
- `.github/workflows/deploy-pages.yml` — публикация фронтенда на GitHub Pages

## Переменные окружения backend

| Переменная | Назначение |
| ---------- | ---------- |
| `DJANGO_SECRET_KEY` | Секрет Django |
| `DJANGO_DEBUG` | `0` для продакшн, `1` для отладки |
| `DJANGO_ALLOWED_HOSTS` | Список доменов через пробел (например, `.koyeb.app`) |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Разрешённые источники CORS, например `https://<username>.github.io` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Источники, которым доверяется CSRF |
| `DATABASE_URL` | Строка подключения к PostgreSQL |
| `GUNICORN_WORKERS` | (необязательно) кол-во воркеров gunicorn |

## API

- Авторизация — POST `/api/auth/token/`
- Профиль текущего пользователя — GET `/api/auth/profile/`
- Сотрудники — GET `/api/employees/`
- Заявки — CRUD `/api/requests/`
- Статусы заявок — GET `/api/requests/statuses/`
- Кампании — GET `/api/campaigns/`

Все эндпоинты защищены аутентификацией (`Authorization: Token <token>`).

## Структура проекта

- `backend/stimul_ico/` — настройки проекта Django
- `backend/stimuli/` — модели, формы, фильтры, шаблоны
- `backend/templates/` — общие шаблоны (включая страницу входа)
- `backend/static/` — стили для серверных шаблонов
- `backend/api/` — REST API (DRF) для статического фронтенда
- `frontend/` — статический клиент, публикуемый на GitHub Pages
- `stimuli/management/commands/` — команды `import_employees` и `setup_roles`

## Примечания

- Денежные значения хранятся в `Decimal` с точностью до двух знаков.
- Возможные статусы заявки: `pending`, `approved`, `rejected`, `archived`.
- Для корректной работы фронтенда обязательно настроить CORS/CSRF на бэкенде.
- Локально удобно запускать Django на `http://127.0.0.1:8000` и указывать этот адрес в `frontend/config.js`.
