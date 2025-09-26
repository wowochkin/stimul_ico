from django import forms

from one_time_payments.models import RequestCampaign
from recurring_payments.models import RecurringPeriod

from .models import Budget, BudgetAllocation


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['budget_type', 'year', 'month', 'total_amount']
        widgets = {
            'year': forms.NumberInput(attrs={'min': 2020}),
            'month': forms.NumberInput(attrs={'min': 1, 'max': 12}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean_total_amount(self):
        total = self.cleaned_data['total_amount']
        if total <= 0:
            raise forms.ValidationError('Сумма бюджета должна быть положительной.')
        return total


class BudgetAllocationForm(forms.ModelForm):
    class Meta:
        model = BudgetAllocation
        fields = ['budget', 'recurring_period', 'campaign', 'allocated_amount']
        widgets = {
            'allocated_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recurring_period'].queryset = RecurringPeriod.objects.order_by('-start_date')
        self.fields['campaign'].queryset = RequestCampaign.objects.order_by('-opens_at')

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('recurring_period')
        campaign = cleaned_data.get('campaign')
        if period and campaign:
            self.add_error('campaign', 'Укажите период или кампанию, но не оба значения одновременно.')
        if not period and not campaign:
            raise forms.ValidationError('Необходимо выбрать период или кампанию для распределения бюджета.')
        allocated = cleaned_data.get('allocated_amount') or 0
        if allocated <= 0:
            self.add_error('allocated_amount', 'Размер выделенного бюджета должен быть положительным.')
        return cleaned_data
