from django import forms

from .models import PositionQuota, PositionQuotaVersion


class PositionQuotaForm(forms.ModelForm):
    class Meta:
        model = PositionQuota
        fields = ['division', 'position', 'total_fte', 'occupied_fte', 'vacant_fte', 'comment']
        widgets = {
            'total_fte': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'occupied_fte': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'vacant_fte': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'comment': forms.TextInput(attrs={'placeholder': 'Комментарий (необязательно)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_fte') or 0
        occupied = cleaned_data.get('occupied_fte') or 0
        vacant = cleaned_data.get('vacant_fte') or 0
        if occupied < 0 or vacant < 0:
            raise forms.ValidationError('Количество ставок не может быть отрицательным.')
        if occupied + vacant > total:
            raise forms.ValidationError('Сумма занятых и вакантных ставок не может превышать общее количество.')
        return cleaned_data


class PositionQuotaVersionForm(forms.ModelForm):
    class Meta:
        model = PositionQuotaVersion
        fields = ['effective_from', 'effective_to', 'total_fte', 'occupied_fte', 'vacant_fte']
        widgets = {
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'type': 'date'}),
            'total_fte': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'occupied_fte': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
            'vacant_fte': forms.NumberInput(attrs={'step': '0.001', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_fte') or 0
        occupied = cleaned_data.get('occupied_fte') or 0
        vacant = cleaned_data.get('vacant_fte') or 0
        if occupied < 0 or vacant < 0:
            raise forms.ValidationError('Количество ставок не может быть отрицательным.')
        if occupied + vacant > total:
            raise forms.ValidationError('Сумма занятых и вакантных ставок не может превышать общее количество.')
        return cleaned_data
