# Деплой системы прав доступа

## Подготовка к деплою

### 1. Миграции

Все необходимые миграции уже созданы и применены:
- `0007_userdivision` - модель для связи пользователей с подразделениями
- `0008_employee_user` - поле user в модели Employee

### 2. Инициализация системы прав доступа

После деплоя выполните команду для создания групп пользователей:

```bash
python manage.py init_permissions
```

Эта команда:
- Создает группы "Руководитель департамента" и "Сотрудник"
- Назначает соответствующие права доступа
- Безопасна для повторного выполнения

### 3. Создание пользователей

#### Создание руководителя департамента:

```bash
python manage.py create_production_user \
  --username "ivan.petrov" \
  --password "secure_password123" \
  --first-name "Иван" \
  --last-name "Петров" \
  --email "ivan.petrov@company.com" \
  --role "manager" \
  --division "Отдел разработки" \
  --position "Руководитель отдела"
```

#### Создание сотрудника:

```bash
python manage.py create_production_user \
  --username "anna.sidorova" \
  --password "secure_password123" \
  --first-name "Анна" \
  --last-name "Сидорова" \
  --email "anna.sidorova@company.com" \
  --role "employee" \
  --division "Отдел разработки" \
  --position "Разработчик"
```

### 4. Проверка работы

После создания пользователей проверьте:

```bash
# Проверить группы
python manage.py shell -c "
from django.contrib.auth.models import Group
for group in Group.objects.all():
    print(f'{group.name}: {group.permissions.count()} прав')
"

# Проверить связи пользователей
python manage.py shell -c "
from django.contrib.auth.models import User
from stimuli.models import Employee, UserDivision
for user in User.objects.all():
    try:
        emp = user.employee_profile
        print(f'✓ {user.username} -> {emp.full_name} ({emp.division.name})')
    except:
        print(f'✗ {user.username} -> НЕТ СВЯЗИ')
"
```

## Миграция существующих данных

### Если у вас уже есть пользователи и сотрудники

1. **Создайте группы:**
```bash
python manage.py init_permissions
```

2. **Свяжите существующих пользователей с сотрудниками:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from stimuli.models import Employee
from staffing.models import Division, Position

# Пример для существующего пользователя
user = User.objects.get(username='existing_user')
division = Division.objects.get(name='Существующее подразделение')
position = Position.objects.get(name='Существующая должность')

# Создаем запись сотрудника
Employee.objects.create(
    user=user,
    full_name=f'{user.first_name} {user.last_name}',
    division=division,
    position=position,
    category=Employee.Category.PPS
)
"
```

3. **Назначьте группы пользователям:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User, Group

# Для руководителя
user = User.objects.get(username='manager_username')
group = Group.objects.get(name='Руководитель департамента')
user.groups.add(group)

# Для сотрудника
user = User.objects.get(username='employee_username')
group = Group.objects.get(name='Сотрудник')
user.groups.add(group)
"
```

4. **Создайте связи с подразделениями для руководителей:**
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from stimuli.models import UserDivision
from staffing.models import Division

user = User.objects.get(username='manager_username')
division = Division.objects.get(name='Подразделение руководителя')
UserDivision.objects.create(user=user, division=division)
"
```

## Проверка на продакшене

### 1. Тестирование прав доступа

1. Войдите как руководитель департамента
2. Попробуйте создать заявку - должны видеть сотрудников своего подразделения
3. Войдите как сотрудник
4. Попробуйте создать заявку - должны видеть только себя

### 2. Проверка в админке

1. Зайдите в админку Django
2. Проверьте раздел "Сотрудники" - у каждого должен быть указан пользователь
3. Проверьте раздел "Подразделения пользователей" - должны быть записи для руководителей

### 3. Логи и мониторинг

Следите за логами на предмет ошибок:
- Ошибки доступа к заявкам
- Проблемы с фильтрацией сотрудников
- Ошибки в формах создания заявок

## Откат изменений (если необходимо)

Если нужно откатить изменения:

```bash
# Откатить миграции
python manage.py migrate stimuli 0006

# Удалить группы
python manage.py shell -c "
from django.contrib.auth.models import Group
Group.objects.filter(name__in=['Руководитель департамента', 'Сотрудник']).delete()
"
```

## Безопасность

- Используйте сильные пароли для пользователей
- Регулярно проверяйте права доступа
- Мониторьте активность пользователей
- Делайте резервные копии перед изменениями
