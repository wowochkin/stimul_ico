from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from staffing.models import Division, Position
from stimuli.models import Employee


class Command(BaseCommand):
    help = 'Обновляет существующих пользователей, добавляя им записи Employee'

    def handle(self, *args, **options):
        # Получаем подразделения и должности
        try:
            division_dev = Division.objects.get(name='Отдел разработки')
            division_marketing = Division.objects.get(name='Отдел маркетинга')
            position_manager = Position.objects.get(name='Руководитель отдела')
            position_dev = Position.objects.get(name='Разработчик')
            position_marketing = Position.objects.get(name='Маркетолог')
        except (Division.DoesNotExist, Position.DoesNotExist) as e:
            self.stdout.write(
                self.style.ERROR(f'Не найдены необходимые подразделения или должности: {e}')
            )
            return
        
        # Обновляем manager_dev
        try:
            user = User.objects.get(username='manager_dev')
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'{user.first_name} {user.last_name}',
                    'division': division_dev,
                    'position': position_manager,
                    'category': Employee.Category.AUP
                }
            )
            if created:
                self.stdout.write(f'Создана запись Employee для {user.username}')
            else:
                self.stdout.write(f'Запись Employee для {user.username} уже существует')
        except User.DoesNotExist:
            self.stdout.write(f'Пользователь manager_dev не найден')
        
        # Обновляем employee_dev
        try:
            user = User.objects.get(username='employee_dev')
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'{user.first_name} {user.last_name}',
                    'division': division_dev,
                    'position': position_dev,
                    'category': Employee.Category.PPS
                }
            )
            if created:
                self.stdout.write(f'Создана запись Employee для {user.username}')
            else:
                self.stdout.write(f'Запись Employee для {user.username} уже существует')
        except User.DoesNotExist:
            self.stdout.write(f'Пользователь employee_dev не найден')
        
        # Обновляем manager_marketing
        try:
            user = User.objects.get(username='manager_marketing')
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'{user.first_name} {user.last_name}',
                    'division': division_marketing,
                    'position': position_manager,
                    'category': Employee.Category.AUP
                }
            )
            if created:
                self.stdout.write(f'Создана запись Employee для {user.username}')
            else:
                self.stdout.write(f'Запись Employee для {user.username} уже существует')
        except User.DoesNotExist:
            self.stdout.write(f'Пользователь manager_marketing не найден')
        
        self.stdout.write(
            self.style.SUCCESS('Обновление пользователей завершено!')
        )
