from django import forms

from staffing.models import Division
from stimuli.models import Employee


class DashboardFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    division = forms.ModelChoiceField(required=False, queryset=Division.objects.order_by('name'))
    employee = forms.ModelChoiceField(required=False, queryset=Employee.objects.order_by('full_name'))

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'Дата окончания не может быть раньше даты начала.')
        return cleaned_data
