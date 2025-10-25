from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from staffing.models import Division, Position
from stimuli.models import UserDivision, Employee


class Command(BaseCommand):
    help = 'Создает пользователей для продакшена (без тестовых данных)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Имя пользователя',
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Пароль пользователя',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            required=True,
            help='Имя',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            required=True,
            help='Фамилия',
        )
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['manager', 'employee'],
            required=True,
            help='Роль пользователя (manager или employee)',
        )
        parser.add_argument(
            '--division',
            type=str,
            help='Название подразделения (обязательно для руководителей)',
        )
        parser.add_argument(
            '--position',
            type=str,
            help='Название должности',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        email = options['email']
        role = options['role']
        division_name = options.get('division')
        position_name = options.get('position')

        # Проверяем, что пользователь не существует
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'Пользователь {username} уже существует!')
            )
            return

        # Получаем группы
        try:
            manager_group = Group.objects.get(name='Руководитель департамента')
            employee_group = Group.objects.get(name='Сотрудник')
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Группы пользователей не найдены! Сначала выполните: python manage.py init_permissions')
            )
            return

        # Создаем пользователя
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            is_active=True,
        )

        if role == 'manager':
            user.groups.add(manager_group)
            
            if not division_name:
                self.stdout.write(
                    self.style.ERROR('Для руководителя обязательно указать подразделение!')
                )
                user.delete()
                return
            
            # Получаем или создаем подразделение
            division, created = Division.objects.get_or_create(name=division_name)
            if created:
                self.stdout.write(f'✓ Создано подразделение: {division_name}')
            
            # Создаем связь с подразделением
            UserDivision.objects.create(user=user, division=division)
            
            # Создаем запись сотрудника
            if position_name:
                position, created = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'base_salary': 100000}
                )
                if created:
                    self.stdout.write(f'✓ Создана должность: {position_name}')
            else:
                position, created = Position.objects.get_or_create(
                    name='Руководитель',
                    defaults={'base_salary': 150000}
                )
            
            Employee.objects.create(
                user=user,
                full_name=f'{first_name} {last_name}',
                division=division,
                position=position,
                category=Employee.Category.AUP
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Создан руководитель департамента: {username}')
            )
            
        else:  # employee
            user.groups.add(employee_group)
            
            if not division_name:
                self.stdout.write(
                    self.style.ERROR('Для сотрудника обязательно указать подразделение!')
                )
                user.delete()
                return
            
            # Получаем или создаем подразделение
            division, created = Division.objects.get_or_create(name=division_name)
            if created:
                self.stdout.write(f'✓ Создано подразделение: {division_name}')
            
            # Создаем запись сотрудника
            if position_name:
                position, created = Position.objects.get_or_create(
                    name=position_name,
                    defaults={'base_salary': 80000}
                )
                if created:
                    self.stdout.write(f'✓ Создана должность: {position_name}')
            else:
                position, created = Position.objects.get_or_create(
                    name='Сотрудник',
                    defaults={'base_salary': 80000}
                )
            
            Employee.objects.create(
                user=user,
                full_name=f'{first_name} {last_name}',
                division=division,
                position=position,
                category=Employee.Category.PPS
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Создан сотрудник: {username}')
            )

        self.stdout.write(f'\n📋 Пользователь {username} успешно создан!')
        self.stdout.write(f'Роль: {"Руководитель департамента" if role == "manager" else "Сотрудник"}')
        self.stdout.write(f'Подразделение: {division_name}')
        if position_name:
            self.stdout.write(f'Должность: {position_name}')
