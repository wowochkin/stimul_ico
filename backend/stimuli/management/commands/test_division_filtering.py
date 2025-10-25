from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stimuli.views import StimulusRequestBulkCreateView
from stimuli.permissions import is_department_manager, get_user_division
from staffing.models import Division


class Command(BaseCommand):
    help = 'Тестирует фильтрацию подразделений в форме массового создания заявок'

    def handle(self, *args, **options):
        self.stdout.write('=== Тестирование фильтрации подразделений ===')
        
        # Создаем фиктивный request объект для тестирования
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        # Тестируем для каждого пользователя
        test_users = ['manager_dev', 'employee_dev', 'manager_marketing', 'employee_marketing']
        
        for username in test_users:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'\nПользователь: {username}')
                
                # Создаем экземпляр view
                view = StimulusRequestBulkCreateView()
                view.request = MockRequest(user)
                
                # Получаем доступные подразделения
                divisions = view.get_divisions()
                
                self.stdout.write(f'  Доступные подразделения: {divisions.count()}')
                for div in divisions:
                    self.stdout.write(f'    - {div.name}')
                
                # Проверяем права
                if is_department_manager(user):
                    user_division = get_user_division(user)
                    if user_division:
                        self.stdout.write(f'  Ожидается: только {user_division.name}')
                        if divisions.count() == 1 and divisions.first().id == user_division.id:
                            self.stdout.write('  ✅ ПРАВИЛЬНО')
                        else:
                            self.stdout.write('  ❌ ОШИБКА')
                    else:
                        self.stdout.write('  ❌ Нет подразделения для руководителя')
                else:
                    self.stdout.write('  Ожидается: пустой список')
                    if divisions.count() == 0:
                        self.stdout.write('  ✅ ПРАВИЛЬНО')
                    else:
                        self.stdout.write('  ❌ ОШИБКА')
                        
            except User.DoesNotExist:
                self.stdout.write(f'\nПользователь {username} не найден')
        
        self.stdout.write('\n=== Общая статистика ===')
        self.stdout.write(f'Всего подразделений в системе: {Division.objects.count()}')
        for div in Division.objects.all():
            self.stdout.write(f'  - {div.name}')
