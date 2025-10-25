from django.core.management.base import BaseCommand
from stimuli.models import Employee
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Очищает дублирующиеся записи сотрудников'

    def handle(self, *args, **options):
        # Удаляем всех сотрудников
        Employee.objects.all().delete()
        
        # Создаем заново только нужных сотрудников
        from staffing.models import Division, Position
        
        division_dev = Division.objects.get(name='Отдел разработки')
        division_marketing = Division.objects.get(name='Отдел маркетинга')
        position_manager = Position.objects.get(name='Руководитель отдела')
        position_dev = Position.objects.get(name='Разработчик')
        position_marketing = Position.objects.get(name='Маркетолог')
        
        # Создаем сотрудников для каждого пользователя
        users_data = [
            ('manager_dev', 'Иван', 'Петров', division_dev, position_manager, Employee.Category.AUP),
            ('employee_dev', 'Анна', 'Сидорова', division_dev, position_dev, Employee.Category.PPS),
            ('manager_marketing', 'Мария', 'Козлова', division_marketing, position_manager, Employee.Category.AUP),
            ('employee_marketing', 'Дмитрий', 'Иванов', division_marketing, position_marketing, Employee.Category.PPS),
        ]
        
        for username, first_name, last_name, division, position, category in users_data:
            try:
                user = User.objects.get(username=username)
                Employee.objects.create(
                    user=user,
                    full_name=f'{first_name} {last_name}',
                    division=division,
                    position=position,
                    category=category
                )
                self.stdout.write(f'✓ Создан сотрудник для {username}')
            except User.DoesNotExist:
                self.stdout.write(f'✗ Пользователь {username} не найден')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nВсего сотрудников: {Employee.objects.count()}')
        )
