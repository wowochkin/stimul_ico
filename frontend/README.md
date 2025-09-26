# Статический фронтенд

Эта директория содержит статическое приложение, которое развёртывается на GitHub Pages и взаимодействует с Django API.

## Локальный запуск

1. Создайте файл `config.js` (на основе `config.template.js`) и укажите базовый адрес API:
   ```js
   window.STIMUL_API_BASE_URL = 'http://127.0.0.1:8000';
   ```
2. Откройте `index.html` в браузере.

## Продакшн

Workflow `.github/workflows/deploy-pages.yml` копирует содержимое директории в артефакт и подставляет адрес API из переменной `PAGES_API_BASE_URL`, формируя файл `config.js` на лету.
