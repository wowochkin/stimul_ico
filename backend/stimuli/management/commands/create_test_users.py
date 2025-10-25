from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from staffing.models import Division, Position
from stimuli.models import UserDivision, Employee


class Command(BaseCommand):
    help = 'Создает тестовых пользователей для демонстрации системы прав доступа'

    def handle(self, *args, **options):
        # Получаем группы
        manager_group = Group.objects.get(name='Руководитель департамента')
        employee_group = Group.objects.get(name='Сотрудник')
        
        # Получаем или создаем подразделения
        division1, created = Division.objects.get_or_create(name='Отдел разработки')
        if created:
            self.stdout.write(f'Создано подразделение: {division1.name}')
        
        division2, created = Division.objects.get_or_create(name='Отдел маркетинга')
        if created:
            self.stdout.write(f'Создано подразделение: {division2.name}')
        
        # Получаем или создаем должности
        position_dev, created = Position.objects.get_or_create(
            name='Разработчик',
            defaults={'base_salary': 100000}
        )
        if created:
            self.stdout.write(f'Создана должность: {position_dev.name}')
        
        position_manager, created = Position.objects.get_or_create(
            name='Руководитель отдела',
            defaults={'base_salary': 150000}
        )
        if created:
            self.stdout.write(f'Создана должность: {position_manager.name}')
        
        position_marketing, created = Position.objects.get_or_create(
            name='Маркетолог',
            defaults={'base_salary': 80000}
        )
        if created:
            self.stdout.write(f'Создана должность: {position_marketing.name}')
        
        # Создаем руководителя департамента
        manager_user, created = User.objects.get_or_create(
            username='manager_dev',
            defaults={
                'first_name': 'Иван',
                'last_name': 'Петров',
                'email': 'manager.dev@example.com',
                'password': make_password('password123'),
                'is_active': True,
            }
        )
        
        if created:
            manager_user.groups.add(manager_group)
            UserDivision.objects.create(user=manager_user, division=division1)
            
            # Создаем запись сотрудника для руководителя
            Employee.objects.create(
                user=manager_user,
                full_name=f'{manager_user.first_name} {manager_user.last_name}',
                division=division1,
                position=position_manager,
                category=Employee.Category.AUP
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Создан руководитель департамента: {manager_user.username}')
            )
        else:
            self.stdout.write(f'Руководитель департамента {manager_user.username} уже существует')
        
        # Создаем сотрудника
        employee_user, created = User.objects.get_or_create(
            username='employee_dev',
            defaults={
                'first_name': 'Анна',
                'last_name': 'Сидорова',
                'email': 'employee.dev@example.com',
                'password': make_password('password123'),
                'is_active': True,
            }
        )
        
        if created:
            employee_user.groups.add(employee_group)
            
            # Создаем запись сотрудника
            Employee.objects.create(
                user=employee_user,
                full_name=f'{employee_user.first_name} {employee_user.last_name}',
                division=division1,
                position=position_dev,
                category=Employee.Category.PPS
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Создан сотрудник: {employee_user.username}')
            )
        else:
            self.stdout.write(f'Сотрудник {employee_user.username} уже существует')
        
        # Создаем еще одного руководителя для другого департамента
        manager2_user, created = User.objects.get_or_create(
            username='manager_marketing',
            defaults={
                'first_name': 'Мария',
                'last_name': 'Козлова',
                'email': 'manager.marketing@example.com',
                'password': make_password('password123'),
                'is_active': True,
            }
        )
        
        if created:
            manager2_user.groups.add(manager_group)
            UserDivision.objects.create(user=manager2_user, division=division2)
            
            # Создаем запись сотрудника для руководителя
            Employee.objects.create(
                user=manager2_user,
                full_name=f'{manager2_user.first_name} {manager2_user.last_name}',
                division=division2,
                position=position_manager,
                category=Employee.Category.AUP
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Создан руководитель департамента: {manager2_user.username}')
            )
        else:
            self.stdout.write(f'Руководитель департамента {manager2_user.username} уже существует')
        
        # Создаем еще одного сотрудника для отдела маркетинга
        employee2_user, created = User.objects.get_or_create(
            username='employee_marketing',
            defaults={
                'first_name': 'Дмитрий',
                'last_name': 'Иванов',
                'email': 'employee.marketing@example.com',
                'password': make_password('password123'),
                'is_active': True,
            }
        )
        
        if created:
            employee2_user.groups.add(employee_group)
            
            # Создаем запись сотрудника
            Employee.objects.create(
                user=employee2_user,
                full_name=f'{employee2_user.first_name} {employee2_user.last_name}',
                division=division2,
                position=position_marketing,
                category=Employee.Category.PPS
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Создан сотрудник: {employee2_user.username}')
            )
        else:
            self.stdout.write(f'Сотрудник {employee2_user.username} уже существует')
        
        self.stdout.write(
            self.style.SUCCESS('\nТестовые пользователи созданы!')
        )
        self.stdout.write('Логины и пароли:')
        self.stdout.write('manager_dev / password123 - Руководитель отдела разработки')
        self.stdout.write('manager_marketing / password123 - Руководитель отдела маркетинга')
        self.stdout.write('employee_dev / password123 - Сотрудник отдела разработки')
        self.stdout.write('employee_marketing / password123 - Сотрудник отдела маркетинга')
