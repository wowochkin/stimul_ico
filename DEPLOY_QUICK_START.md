# Краткая инструкция по деплою системы прав доступа

## Что нужно сделать на деплое

### 1. После деплоя на Koyeb

Выполните в Web Console:

```bash
# Инициализация системы прав доступа
python backend/manage.py init_permissions

# Создание администратора
python backend/manage.py create_production_user \
  --username "admin" \
  --password "your_secure_password" \
  --first-name "Админ" \
  --last-name "Админов" \
  --email "admin@yourcompany.com" \
  --role "manager" \
  --division "Администрация" \
  --position "Администратор"
```

### 2. Создание пользователей для каждого отдела

```bash
# Руководитель отдела разработки
python backend/manage.py create_production_user \
  --username "manager.dev" \
  --password "secure_password" \
  --first-name "Иван" \
  --last-name "Петров" \
  --email "manager.dev@company.com" \
  --role "manager" \
  --division "Отдел разработки" \
  --position "Руководитель отдела"

# Сотрудник отдела разработки
python backend/manage.py create_production_user \
  --username "employee.dev" \
  --password "secure_password" \
  --first-name "Анна" \
  --last-name "Сидорова" \
  --email "employee.dev@company.com" \
  --role "employee" \
  --division "Отдел разработки" \
  --position "Разработчик"
```

### 3. Проверка работы

1. Зайдите в админку Django
2. Проверьте раздел "Сотрудники" - у каждого должен быть указан пользователь
3. Проверьте раздел "Подразделения пользователей" - должны быть записи для руководителей
4. Протестируйте создание заявок под разными пользователями

### 4. Если что-то пошло не так

```bash
# Очистить и пересоздать все связи
python backend/manage.py reset_user_connections --clean

# Или только очистить дублирующиеся записи
python backend/manage.py clean_employees
```

## Важные моменты

- **Руководители департамента** видят только сотрудников своего подразделения
- **Сотрудники** видят только себя
- Все связи настраиваются автоматически при создании пользователей
- Система безопасна для повторного выполнения команд

## Документация

- `DEPLOYMENT_GUIDE.md` - подробная инструкция по деплою
- `USER_PERMISSIONS.md` - техническая документация системы прав
- `PERMISSIONS_GUIDE.md` - краткая инструкция по использованию
- `TROUBLESHOOTING.md` - решение проблем
