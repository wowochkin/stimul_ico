from django.core.management.base import BaseCommand
from staffing.models import Division, Position


class Command(BaseCommand):
    help = 'Создает основные подразделения и должности для работы системы'

    def handle(self, *args, **options):
        # Список основных подразделений из ошибки пользователя
        divisions = [
            'ИЦО',
            'Департамент информатики, управления и технологий',
            'Департамент информатизации образования',
            'Департамент математики и физики',
            'Офис учебно-методического сопровождения образовательного процесса',
        ]
        
        # Список основных должностей
        positions = [
            'Руководитель департамента',
            'Заместитель руководителя',
            'Начальник отдела',
            'Старший преподаватель',
            'Преподаватель',
            'Доцент',
            'Профессор',
            'Старший научный сотрудник',
            'Научный сотрудник',
            'Инженер',
            'Программист',
            'Системный администратор',
            'Методист',
            'Специалист',
        ]
        
        created_divisions = 0
        created_positions = 0
        
        # Создаем подразделения
        for division_name in divisions:
            division_obj, created = Division.objects.get_or_create(name=division_name)  # noqa: E501
            if created:
                created_divisions += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Создано подразделение: {division_name}'))  # noqa: E501
            else:
                self.stdout.write(f'Подразделение уже существует: {division_name}')
        
        # Создаем должности
        for position_name in positions:
            position_obj, created = Position.objects.get_or_create(  # noqa: E501
                name=position_name,
                defaults={'base_salary': 0}
            )
            if created:
                created_positions += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Создана должность: {position_name}'))  # noqa: E501
            else:
                self.stdout.write(f'Должность уже существует: {position_name}')
        
        # Итоговая статистика
        self.stdout.write(self.style.SUCCESS(f'\n✓ Обработка завершена:'))
        self.stdout.write(f'Создано подразделений: {created_divisions}')
        self.stdout.write(f'Создано должностей: {created_positions}')
        
        if created_divisions == 0 and created_positions == 0:
            self.stdout.write(self.style.WARNING('Все подразделения и должности уже существуют в базе данных.'))
        else:
            self.stdout.write(self.style.SUCCESS('Теперь можно загружать Excel файл с сотрудниками!'))
