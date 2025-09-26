from django import forms

from .models import RecurringPayment, RecurringPeriod


class RecurringPeriodForm(forms.ModelForm):
    class Meta:
        model = RecurringPeriod
        fields = ['name', 'start_date', 'end_date', 'budget_limit', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'Дата окончания не может быть раньше даты начала.')
        return cleaned_data


class RecurringPaymentForm(forms.ModelForm):
    class Meta:
        model = RecurringPayment
        fields = ['amount', 'reason', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'reason': forms.TextInput(attrs={'placeholder': 'Основание выплаты'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Комментарий (необязательно)'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Сумма должна быть больше нуля.')
        return amount

    def clean_reason(self):
        reason = (self.cleaned_data.get('reason') or '').strip()
        if not reason:
            raise forms.ValidationError('Укажите основание выплаты.')
        return reason


class RecurringPeriodCloseForm(forms.Form):
    reason = forms.CharField(
        label='Комментарий к закрытию',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
