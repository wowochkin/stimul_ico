from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from one_time_payments.models import RequestCampaign
from stimuli.forms import StimulusRequestForm
from stimuli.permissions import can_change_request_status
from stimuli.models import StimulusRequest


class Command(BaseCommand):
    help = 'Тестирует ограничения доступа для сотрудников'

    def handle(self, *args, **options):
        self.stdout.write('=== Тестирование ограничений доступа ===')
        
        # Создаем фиктивный request объект для тестирования
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        # Тестируем доступ к кампаниям
        self.stdout.write('\n=== Тестирование доступа к кампаниям ===')
        
        # Создаем тестовые кампании
        campaign_open, _ = RequestCampaign.objects.get_or_create(
            name='Тестовая открытая кампания',
            defaults={
                'status': RequestCampaign.Status.OPEN,
                'opens_at': '2024-01-01',
                'description': 'Тестовая кампания'
            }
        )
        
        campaign_closed, _ = RequestCampaign.objects.get_or_create(
            name='Тестовая закрытая кампания',
            defaults={
                'status': RequestCampaign.Status.CLOSED,
                'opens_at': '2024-01-01',
                'description': 'Тестовая кампания'
            }
        )
        
        campaign_archived, _ = RequestCampaign.objects.get_or_create(
            name='Тестовая архивная кампания',
            defaults={
                'status': RequestCampaign.Status.ARCHIVED,
                'opens_at': '2024-01-01',
                'description': 'Тестовая кампания'
            }
        )
        
        # Тестируем для каждого пользователя
        test_users = ['manager_dev', 'employee_dev', 'manager_marketing', 'employee_marketing']
        
        for username in test_users:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'\nПользователь: {username}')
                
                # Создаем форму
                form = StimulusRequestForm(user=user)
                campaigns = form.fields['campaign'].queryset
                
                self.stdout.write(f'  Доступные кампании: {campaigns.count()}')
                for campaign in campaigns:
                    self.stdout.write(f'    - {campaign.name} ({campaign.get_status_display()})')
                
                # Проверяем права
                if username.startswith('employee_'):
                    self.stdout.write('  Ожидается: только открытые кампании')
                    open_campaigns = campaigns.filter(status=RequestCampaign.Status.OPEN)
                    if campaigns.count() == open_campaigns.count() and open_campaigns.count() > 0:
                        self.stdout.write('  ✅ ПРАВИЛЬНО')
                    else:
                        self.stdout.write('  ❌ ОШИБКА')
                else:
                    self.stdout.write('  Ожидается: все кампании кроме черновиков')
                    non_draft_campaigns = campaigns.exclude(status=RequestCampaign.Status.DRAFT)
                    if campaigns.count() == non_draft_campaigns.count():
                        self.stdout.write('  ✅ ПРАВИЛЬНО')
                    else:
                        self.stdout.write('  ❌ ОШИБКА')
                        
            except User.DoesNotExist:
                self.stdout.write(f'\nПользователь {username} не найден')
        
        # Тестируем права на изменение статуса
        self.stdout.write('\n=== Тестирование прав на изменение статуса ===')
        
        # Тестируем для каждой заявки
        test_requests = StimulusRequest.objects.all()[:2]  # Берем первые 2 заявки
        
        for i, test_request in enumerate(test_requests):
            self.stdout.write(f'\nЗаявка {i+1}: {test_request}')
            self.stdout.write(f'  Сотрудник: {test_request.employee.full_name} ({test_request.employee.division.name})')
            self.stdout.write(f'  Создал: {test_request.requested_by.username}')
            
            for username in test_users:
                try:
                    user = User.objects.get(username=username)
                    can_change = can_change_request_status(user, test_request)
                    
                    # Определяем ожидаемый результат
                    if username.startswith('employee_'):
                        expected = False
                        reason = 'сотрудники не могут изменять статус'
                    elif username.startswith('manager_'):
                        # Руководитель может изменять статус только заявок своего подразделения
                        user_division = user.user_division.division if hasattr(user, 'user_division') else None
                        if user_division and test_request.employee.division == user_division:
                            expected = True
                            reason = 'руководитель своего подразделения'
                        else:
                            expected = False
                            reason = 'руководитель другого подразделения'
                    else:
                        expected = False
                        reason = 'неизвестная роль'
                    
                    self.stdout.write(f'  {username}: {can_change} (ожидается {expected} - {reason})')
                    
                    if can_change == expected:
                        self.stdout.write('    ✅ ПРАВИЛЬНО')
                    else:
                        self.stdout.write('    ❌ ОШИБКА')
                        
                except User.DoesNotExist:
                    self.stdout.write(f'  {username}: НЕ НАЙДЕН')
        
        self.stdout.write('\n=== Тестирование завершено ===')
