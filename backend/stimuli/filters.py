import django_filters

from one_time_payments.models import RequestCampaign
from staffing.models import Division, Position
from .models import Employee, StimulusRequest


class EmployeeFilter(django_filters.FilterSet):
    full_name = django_filters.CharFilter(label='ФИО', lookup_expr='icontains')
    division = django_filters.ModelChoiceFilter(label='Подразделение', queryset=Division.objects.none())
    position = django_filters.ModelChoiceFilter(label='Должность', queryset=Position.objects.none())
    category = django_filters.ChoiceFilter(label='Категория', choices=Employee.Category.choices)

    class Meta:
        model = Employee
        fields = ['full_name', 'division', 'position', 'category']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)

        division_field = self.filters['division']
        division_field.field.empty_label = 'Все подразделения'
        division_field.field.queryset = Division.objects.order_by('name')

        position_field = self.filters['position']
        position_field.field.empty_label = 'Все должности'
        position_field.field.queryset = Position.objects.order_by('name')


class StimulusRequestFilter(django_filters.FilterSet):
    employee__full_name = django_filters.CharFilter(label='ФИО сотрудника', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(label='Статус', choices=StimulusRequest.Status.choices)
    campaign = django_filters.ModelChoiceFilter(label='Кампания', queryset=RequestCampaign.objects.none())

    class Meta:
        model = StimulusRequest
        fields = ['employee__full_name', 'status', 'campaign']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)
        self.filters['campaign'].field.empty_label = 'Все кампании'
        
        # Ограничиваем выбор кампаний в зависимости от роли пользователя
        if request and request.user.is_authenticated:
            from stimuli.permissions import is_employee, is_department_manager
            if is_employee(request.user) or is_department_manager(request.user):
                # Сотрудники и руководители департамента видят только открытые кампании
                self.filters['campaign'].field.queryset = RequestCampaign.objects.filter(
                    status=RequestCampaign.Status.OPEN
                ).order_by('-opens_at', 'name')
            else:
                # Администраторы видят все кампании кроме черновиков
                self.filters['campaign'].field.queryset = RequestCampaign.objects.exclude(
                    status=RequestCampaign.Status.DRAFT
                ).order_by('-opens_at', 'name')
        else:
            # По умолчанию показываем все кампании кроме черновиков
            self.filters['campaign'].field.queryset = RequestCampaign.objects.exclude(
                status=RequestCampaign.Status.DRAFT
            ).order_by('-opens_at', 'name')
