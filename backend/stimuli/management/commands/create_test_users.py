from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from staffing.models import Division
from stimuli.models import UserDivision


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
            self.stdout.write(
                self.style.SUCCESS(f'Создан руководитель департамента: {manager2_user.username}')
            )
        else:
            self.stdout.write(f'Руководитель департамента {manager2_user.username} уже существует')
        
        self.stdout.write(
            self.style.SUCCESS('\nТестовые пользователи созданы!')
        )
        self.stdout.write('Логины и пароли:')
        self.stdout.write('manager_dev / password123 - Руководитель отдела разработки')
        self.stdout.write('manager_marketing / password123 - Руководитель отдела маркетинга')
        self.stdout.write('employee_dev / password123 - Сотрудник')
