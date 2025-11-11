from django import forms
from django.core.exceptions import ValidationError

from django.forms import inlineformset_factory

from one_time_payments.models import RequestCampaign

from .models import Employee, InternalAssignment, StimulusRequest


class EmployeeExcelUploadForm(forms.Form):
    """Форма для загрузки Excel файла с данными сотрудников"""
    excel_file = forms.FileField(
        label='Excel файл',
        help_text='Выберите файл Excel (.xlsx, .xls) с данными сотрудников',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls',
            'class': 'form-control-file'
        })
    )
    
    sync_mode = forms.ChoiceField(
        label='Режим синхронизации',
        choices=[
            ('add_update', 'Только добавить/обновить записи'),
            ('full_sync', 'Полная синхронизация (удалить отсутствующие записи)'),
        ],
        initial='add_update',
        widget=forms.RadioSelect,
        help_text='Выберите режим обработки файла'
    )

    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if not file:
            raise ValidationError('Не выбран файл для загрузки.')
        
        # Проверяем расширение файла
        if not file.name.endswith(('.xlsx', '.xls')):
            raise ValidationError('Поддерживаются только файлы Excel (.xlsx, .xls).')
        
        # Проверяем размер файла (10 МБ)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError('Размер файла не должен превышать 10 МБ.')
        
        return file


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'full_name',
            'division',
            'position',
            'category',
            'rate',
            'allowance_amount',
            'allowance_reason',
            'allowance_until',
            'payment',
            'justification',
        ]
        widgets = {
            'justification': forms.Textarea(attrs={'rows': 3}),
            'allowance_reason': forms.Textarea(attrs={'rows': 2}),
            'allowance_until': forms.DateInput(attrs={'type': 'date'}),
            'rate': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'allowance_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'payment': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from staffing.models import Division, Position
        self.fields['division'].queryset = Division.objects.order_by('name')
        self.fields['position'].queryset = Position.objects.order_by('name')

    def clean_payment(self):
        payment = self.cleaned_data['payment']
        if payment < 0:
            raise forms.ValidationError('Выплата не может быть отрицательной.')
        return payment

    def clean_rate(self):
        rate = self.cleaned_data['rate']
        if rate <= 0:
            raise forms.ValidationError('Ставка должна быть больше нуля.')
        return rate

    def clean_allowance_amount(self):
        allowance = self.cleaned_data['allowance_amount']
        if allowance < 0:
            raise forms.ValidationError('Надбавка не может быть отрицательной.')
        return allowance

    def clean(self):
        cleaned_data = super().clean()
        allowance = cleaned_data.get('allowance_amount')
        reason = cleaned_data.get('allowance_reason')
        if allowance and allowance > 0 and not reason:
            self.add_error('allowance_reason', 'Необходимо указать основание при наличии надбавки.')
        return cleaned_data


class StimulusRequestForm(forms.ModelForm):
    class Meta:
        model = StimulusRequest
        fields = ['employee', 'campaign', 'amount', 'justification']
        widgets = {
            'justification': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Опишите обоснование выплаты'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Все пользователи видят только открытые кампании для создания заявок
        self.fields['campaign'].queryset = RequestCampaign.objects.filter(
            status=RequestCampaign.Status.OPEN
        ).order_by('-opens_at', 'name')
        
        self.fields['campaign'].required = True

        if not self.is_bound:
            has_instance_campaign = getattr(self.instance, 'campaign_id', None)
            has_initial_campaign = bool(self.initial.get('campaign'))
            if not has_instance_campaign and not has_initial_campaign:
                default_campaign = RequestCampaign.objects.current()
                if default_campaign:
                    self.initial['campaign'] = default_campaign.pk
                    self.fields['campaign'].initial = default_campaign.pk
        
        # Ограничиваем выбор сотрудников в зависимости от роли пользователя
        if user:
            from .permissions import get_accessible_employees
            self.fields['employee'].queryset = get_accessible_employees(user).order_by('full_name')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Размер выплаты должен быть больше нуля.')
        return amount

    def clean_campaign(self):
        campaign = self.cleaned_data.get('campaign')
        if campaign:
            if campaign.status == RequestCampaign.Status.DRAFT:
                raise forms.ValidationError('Нельзя привязывать заявку к кампании в статусе черновика.')
            if campaign.status != RequestCampaign.Status.OPEN:
                raise forms.ValidationError('Нельзя привязывать заявку к закрытой или архивированной кампании.')
        return campaign


class StimulusRequestStatusForm(forms.ModelForm):
    class Meta:
        model = StimulusRequest
        fields = ['status', 'admin_comment']
        widgets = {
            'admin_comment': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Комментарий для ответственного'}),
        }


InternalAssignmentFormSet = inlineformset_factory(
    Employee,
    InternalAssignment,
    fields=['position', 'rate', 'allowance_amount', 'allowance_reason', 'allowance_until'],
    extra=1,
    can_delete=True,
    widgets={
        'allowance_reason': forms.Textarea(attrs={'rows': 2}),
        'allowance_until': forms.DateInput(attrs={'type': 'date'}),
        'rate': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
        'allowance_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
    }
)
