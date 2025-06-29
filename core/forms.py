from django import forms
from .models import Attendance, User

class ManualAttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['user', 'company', 'timestamp', 'action']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'timestamp': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'action': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)  # request'i al
        super().__init__(*args, **kwargs)

        # Şirket bazlı filtreleme
        if request:
            company = getattr(request.user, 'company', None)
            if company:
                # Sadece o şirketteki kullanıcılar görünsün
                self.fields['user'].queryset = User.objects.filter(company=company)
                # company alanını sabitle (readonly yerine hidden önerilir)
                self.fields['company'].initial = company
                self.fields['company'].widget = forms.HiddenInput()

        # input tipi yeniden güncelleniyor (gerekli değil ama emin olmak için kalabilir)
        self.fields['timestamp'].widget.attrs.update({'type': 'datetime-local'})
