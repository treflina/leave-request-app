from django import forms
from django.db.models import query

from .models import Sickleave
from applications.users.models import User

class SickleaveForm(forms.ModelForm):

    class Meta:

        model = Sickleave
        fields = (
            'employee',
            'type',
            'issue_date',
            'doc_number',
            'start_date',
            'end_date',
            'additional_info',  
        )

        labels = {
            'employee': ('Osoba'),
        }  
        widgets = {
      
            'start_date': forms.DateInput(
                format='%d.%m.%y',
                attrs = {
                    'type': 'date',
                },
                ),
            'end_date': forms.DateInput(
                format='%d.%m.%y',
                attrs = {
                    'type': 'date',
                },
                ),
            'issue_date': forms.DateInput(
                format='%d.%m.%y',
                attrs = {
                    'type': 'date',
                },
                ),
        }

    def __init__(self, *args, **kwargs):
        super(SickleaveForm, self).__init__(*args, **kwargs)
        self.fields['employee'] = forms.ModelChoiceField(
        label='Osoba',
        queryset=User.objects.all())
    