from django import forms
from django.forms import ModelForm, modelformset_factory
from .models import Attendance, User, LeaveRequest,WorkSchedule

class ManualAttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['user', 'timestamp', 'action']  # company çıkarıldı
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'timestamp': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'action': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            company = getattr(self.request.user, 'company', None)
            if company:
                self.fields['user'].queryset = User.objects.filter(company=company)
        self.fields['timestamp'].widget.attrs.update({'type': 'datetime-local'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.request:
            company = getattr(self.request.user, 'company', None)
            if company:
                instance.company = company
        if commit:
            instance.save()
        return instance



class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }


class WorkScheduleForm(forms.ModelForm):
    class Meta:
        model = WorkSchedule
        fields = ['employee', 'week_start_date']
        widgets = {
            'week_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': True}),
            'employee': forms.Select(attrs={'class': 'form-control', 'required': True})
        }

    def clean(self):
        cleaned_data = super().clean()
        # Ek validasyonlar buraya
        return cleaned_data

WorkScheduleFormSet = modelformset_factory(
    WorkSchedule,
    extra=6,
    can_delete=False,
    fields=('day', 'start_time', 'end_time', 'is_active'),
    widgets={
        'day': forms.Select(attrs={
            'class': 'form-control',
            'required': 'required'
        }),
        'start_time': forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'required': 'required'
        }),
        'end_time': forms.TimeInput(attrs={
            'type': 'time', 
            'class': 'form-control',
            'required': 'required'
        }),
        'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
    },
    # Boş formları yoksay
    validate_min=True,
    min_num=1  # En az 1 geçerli form olmalı
)