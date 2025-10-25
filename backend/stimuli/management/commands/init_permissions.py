from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from stimuli.models import StimulusRequest, Employee


class Command(BaseCommand):
    help = 'Инициализирует систему прав доступа на деплое'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Пересоздать группы даже если они уже существуют',
        )

    def handle(self, *args, **options):
        self.stdout.write('Инициализация системы прав доступа...')
        
        # Создаем группы пользователей
        manager_group, created = Group.objects.get_or_create(name='Руководитель департамента')
        if created:
            self.stdout.write('✓ Создана группа "Руководитель департамента"')
        else:
            self.stdout.write('✓ Группа "Руководитель департамента" уже существует')

        employee_group, created = Group.objects.get_or_create(name='Сотрудник')
        if created:
            self.stdout.write('✓ Создана группа "Сотрудник"')
        else:
            self.stdout.write('✓ Группа "Сотрудник" уже существует')

        # Получаем ContentType для моделей
        stimulus_request_ct = ContentType.objects.get_for_model(StimulusRequest)
        employee_ct = ContentType.objects.get_for_model(Employee)

        # Права для руководителя департамента
        manager_permissions = [
            # Права на заявки на стимулирование
            Permission.objects.get(codename='add_stimulusrequest', content_type=stimulus_request_ct),
            Permission.objects.get(codename='view_stimulusrequest', content_type=stimulus_request_ct),
            Permission.objects.get(codename='change_stimulusrequest', content_type=stimulus_request_ct),
            Permission.objects.get(codename='delete_stimulusrequest', content_type=stimulus_request_ct),
            # Кастомные права
            Permission.objects.get(codename='view_all_requests', content_type=stimulus_request_ct),
            Permission.objects.get(codename='edit_pending_requests', content_type=stimulus_request_ct),
            # Права на сотрудников (для просмотра)
            Permission.objects.get(codename='view_employee', content_type=employee_ct),
        ]

        # Права для сотрудника
        employee_permissions = [
            # Права на заявки на стимулирование (только свои)
            Permission.objects.get(codename='add_stimulusrequest', content_type=stimulus_request_ct),
            Permission.objects.get(codename='view_stimulusrequest', content_type=stimulus_request_ct),
            Permission.objects.get(codename='change_stimulusrequest', content_type=stimulus_request_ct),
            Permission.objects.get(codename='delete_stimulusrequest', content_type=stimulus_request_ct),
            # Кастомные права (только для своих заявок)
            Permission.objects.get(codename='edit_pending_requests', content_type=stimulus_request_ct),
        ]

        # Назначаем права группам
        manager_group.permissions.set(manager_permissions)
        self.stdout.write(f'✓ Назначены права группе "Руководитель департамента": {len(manager_permissions)} прав')

        employee_group.permissions.set(employee_permissions)
        self.stdout.write(f'✓ Назначены права группе "Сотрудник": {len(employee_permissions)} прав')

        self.stdout.write(
            self.style.SUCCESS('\n✅ Система прав доступа успешно инициализирована!')
        )
        
        self.stdout.write('\n📋 Следующие шаги:')
        self.stdout.write('1. Создайте пользователей в админке Django')
        self.stdout.write('2. Назначьте им соответствующие группы')
        self.stdout.write('3. Для руководителей департамента создайте записи в "Подразделения пользователей"')
        self.stdout.write('4. Для всех пользователей создайте записи в "Сотрудники" с привязкой к пользователю')
