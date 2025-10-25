from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stimuli.models import Employee, UserDivision
from staffing.models import Division, Position


class Command(BaseCommand):
    help = 'Очищает и правильно настраивает связи между пользователями и сотрудниками'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Удалить всех сотрудников без связи с пользователями',
        )

    def handle(self, *args, **options):
        if options['clean']:
            # Удаляем всех сотрудников без связи с пользователями
            employees_without_users = Employee.objects.filter(user__isnull=True)
            count = employees_without_users.count()
            employees_without_users.delete()
            self.stdout.write(
                self.style.WARNING(f'Удалено {count} сотрудников без связи с пользователями')
            )
        
        # Создаем недостающие подразделения и должности
        division_dev, _ = Division.objects.get_or_create(name='Отдел разработки')
        division_marketing, _ = Division.objects.get_or_create(name='Отдел маркетинга')
        
        position_manager, _ = Position.objects.get_or_create(
            name='Руководитель отдела',
            defaults={'base_salary': 150000}
        )
        position_dev, _ = Position.objects.get_or_create(
            name='Разработчик',
            defaults={'base_salary': 100000}
        )
        position_marketing, _ = Position.objects.get_or_create(
            name='Маркетолог',
            defaults={'base_salary': 80000}
        )
        
        # Создаем пользователей и сотрудников заново
        from django.contrib.auth.models import Group
        from django.contrib.auth.hashers import make_password
        
        manager_group = Group.objects.get(name='Руководитель департамента')
        employee_group = Group.objects.get(name='Сотрудник')
        
        # Удаляем старые записи
        User.objects.filter(username__in=['manager_dev', 'employee_dev', 'manager_marketing', 'employee_marketing']).delete()
        
        # Создаем manager_dev
        manager_user = User.objects.create_user(
            username='manager_dev',
            first_name='Иван',
            last_name='Петров',
            email='manager.dev@example.com',
            password='password123',
            is_active=True,
        )
        manager_user.groups.add(manager_group)
        UserDivision.objects.create(user=manager_user, division=division_dev)
        Employee.objects.create(
            user=manager_user,
            full_name=f'{manager_user.first_name} {manager_user.last_name}',
            division=division_dev,
            position=position_manager,
            category=Employee.Category.AUP
        )
        self.stdout.write(f'✓ Создан manager_dev')
        
        # Создаем employee_dev
        employee_user = User.objects.create_user(
            username='employee_dev',
            first_name='Анна',
            last_name='Сидорова',
            email='employee.dev@example.com',
            password='password123',
            is_active=True,
        )
        employee_user.groups.add(employee_group)
        Employee.objects.create(
            user=employee_user,
            full_name=f'{employee_user.first_name} {employee_user.last_name}',
            division=division_dev,
            position=position_dev,
            category=Employee.Category.PPS
        )
        self.stdout.write(f'✓ Создан employee_dev')
        
        # Создаем manager_marketing
        manager2_user = User.objects.create_user(
            username='manager_marketing',
            first_name='Мария',
            last_name='Козлова',
            email='manager.marketing@example.com',
            password='password123',
            is_active=True,
        )
        manager2_user.groups.add(manager_group)
        UserDivision.objects.create(user=manager2_user, division=division_marketing)
        Employee.objects.create(
            user=manager2_user,
            full_name=f'{manager2_user.first_name} {manager2_user.last_name}',
            division=division_marketing,
            position=position_manager,
            category=Employee.Category.AUP
        )
        self.stdout.write(f'✓ Создан manager_marketing')
        
        # Создаем employee_marketing
        employee2_user = User.objects.create_user(
            username='employee_marketing',
            first_name='Дмитрий',
            last_name='Иванов',
            email='employee.marketing@example.com',
            password='password123',
            is_active=True,
        )
        employee2_user.groups.add(employee_group)
        Employee.objects.create(
            user=employee2_user,
            full_name=f'{employee2_user.first_name} {employee2_user.last_name}',
            division=division_marketing,
            position=position_marketing,
            category=Employee.Category.PPS
        )
        self.stdout.write(f'✓ Создан employee_marketing')
        
        self.stdout.write(
            self.style.SUCCESS('\nВсе пользователи и связи созданы заново!')
        )
        
        # Проверяем результат
        self.stdout.write('\n=== Проверка результата ===')
        for user in User.objects.filter(username__in=['manager_dev', 'employee_dev', 'manager_marketing', 'employee_marketing']):
            try:
                emp = user.employee_profile
                print(f'✓ {user.username} -> {emp.full_name} ({emp.division.name})')
            except:
                print(f'✗ {user.username} -> ОШИБКА')
