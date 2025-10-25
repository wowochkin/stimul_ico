from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stimuli.models import UserDivision, Employee
from stimuli.permissions import is_department_manager, get_user_division


class Command(BaseCommand):
    help = 'Проверяет и исправляет связи между пользователями и сотрудниками'

    def handle(self, *args, **options):
        self.stdout.write('=== Проверка связей ===')
        
        # Проверяем руководителей департамента
        managers = User.objects.filter(groups__name='Руководитель департамента')
        self.stdout.write(f'Руководителей департамента: {managers.count()}')
        
        for user in managers:
            self.stdout.write(f'\nПользователь: {user.username}')
            self.stdout.write(f'  is_department_manager: {is_department_manager(user)}')
            
            try:
                division = get_user_division(user)
                if division:
                    self.stdout.write(f'  Подразделение: {division.name}')
                else:
                    self.stdout.write('  Подразделение: НЕ НАЗНАЧЕНО')
            except Exception as e:
                self.stdout.write(f'  Ошибка: {e}')
            
            try:
                emp = user.employee_profile
                self.stdout.write(f'  Сотрудник: {emp.full_name}')
            except Exception as e:
                self.stdout.write(f'  Сотрудник: НЕТ СВЯЗИ - {e}')
        
        # Проверяем сотрудников
        employees = User.objects.filter(groups__name='Сотрудник')
        self.stdout.write(f'\nСотрудников: {employees.count()}')
        
        for user in employees:
            self.stdout.write(f'\nПользователь: {user.username}')
            try:
                emp = user.employee_profile
                self.stdout.write(f'  Сотрудник: {emp.full_name} ({emp.division.name})')
            except Exception as e:
                self.stdout.write(f'  Сотрудник: НЕТ СВЯЗИ - {e}')
        
        # Проверяем UserDivision
        self.stdout.write(f'\nСвязей UserDivision: {UserDivision.objects.count()}')
        for ud in UserDivision.objects.all():
            self.stdout.write(f'  {ud.user.username} -> {ud.division.name}')
        
        # Проверяем Employee с пользователями
        employees_with_users = Employee.objects.filter(user__isnull=False)
        self.stdout.write(f'\nСотрудников с пользователями: {employees_with_users.count()}')
        for emp in employees_with_users:
            self.stdout.write(f'  {emp.full_name} -> {emp.user.username}')
