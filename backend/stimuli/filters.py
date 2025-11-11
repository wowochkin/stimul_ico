import django_filters
from django.contrib.auth import get_user_model

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
    status = django_filters.MultipleChoiceFilter(
        label='Статус',
        choices=StimulusRequest.Status.choices,
        field_name='status',
        lookup_expr='in'
    )
    campaign = django_filters.ModelChoiceFilter(label='Кампания', queryset=RequestCampaign.objects.none())
    requested_by = django_filters.ModelMultipleChoiceFilter(
        label='Ответственный',
        queryset=get_user_model().objects.none(),
        field_name='requested_by',
        to_field_name='id'
    )

    class Meta:
        model = StimulusRequest
        fields = ['status', 'campaign', 'requested_by']

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

        requested_by_filter = self.filters['requested_by']
        if queryset is not None:
            user_ids = queryset.values_list('requested_by_id', flat=True).distinct()
            requested_by_filter.field.queryset = get_user_model().objects.filter(
                id__in=user_ids
            ).order_by('last_name', 'first_name', 'username')
        else:
            requested_by_filter.field.queryset = get_user_model().objects.none()


class CampaignStimulusRequestFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        label='Статус',
        choices=StimulusRequest.Status.choices,
        field_name='status',
        lookup_expr='in'
    )
    requested_by = django_filters.ModelMultipleChoiceFilter(
        label='Ответственный',
        queryset=get_user_model().objects.none(),
        field_name='requested_by',
        to_field_name='id'
    )

    class Meta:
        model = StimulusRequest
        fields = ['status', 'requested_by']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(data, queryset, request=request, prefix=prefix)

        requested_by_filter = self.filters['requested_by']
        requested_by_filter.field.empty_label = 'Все ответственные'

        qs = queryset or StimulusRequest.objects.none()
        user_ids = qs.values_list('requested_by_id', flat=True).distinct()
        UserModel = get_user_model()
        requested_by_filter.field.queryset = UserModel.objects.filter(id__in=user_ids).order_by('last_name', 'first_name', 'username')
