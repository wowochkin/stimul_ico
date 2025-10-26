from django import forms

from stimuli.models import Employee

from .models import OneTimePayment, RequestCampaign


class RequestCampaignForm(forms.ModelForm):
    class Meta:
        model = RequestCampaign
        fields = ['name', 'description', 'opens_at', 'deadline', 'auto_close_day', 'auto_close_enabled']
        widgets = {
            'opens_at': forms.DateInput(attrs={'type': 'date'}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Описание кампании'}),
        }

    def clean_deadline(self):
        opens_at = self.cleaned_data.get('opens_at')
        deadline = self.cleaned_data.get('deadline')
        if opens_at and deadline and deadline < opens_at:
            raise forms.ValidationError('Дедлайн не может быть раньше даты открытия.')
        return deadline


class RequestCampaignStatusForm(forms.Form):
    action = forms.ChoiceField(
        choices=[
            ('open', 'Открыть'),
            ('close', 'Закрыть'),
            ('reopen', 'Переоткрыть'),
            ('archive', 'Переместить в архив'),
        ]
    )


class OneTimePaymentForm(forms.ModelForm):
    class Meta:
        model = OneTimePayment
        fields = ['employee', 'amount', 'payment_date', 'campaign', 'justification']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'justification': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Укажите основание выплаты'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.order_by('full_name')
        self.fields['campaign'].queryset = RequestCampaign.objects.order_by('-opens_at', 'name')
        self.fields['campaign'].required = False

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Сумма должна быть положительной.')
        return amount

    def clean_campaign(self):
        campaign = self.cleaned_data.get('campaign')
        if campaign and campaign.status == RequestCampaign.Status.DRAFT:
            raise forms.ValidationError('Нельзя привязать выплату к кампании в статусе черновика.')
        return campaign
