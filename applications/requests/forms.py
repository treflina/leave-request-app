from datetime import datetime, date
from crispy_forms.helper import FormHelper

from django.db.models.fields import DateField
from django.forms.fields import ChoiceField
from django.forms.widgets import Select, SelectDateWidget

from django import forms

from .models import Request, User


class RequestForm(forms.ModelForm):

    class Meta:
        model=Request
        fields = (
            'send_to_person',
            'type',
            'work_date',
            'start_date',
            'end_date',
            'days',
            'substitute',
        )
        widgets = {
            'send_to_person': forms.Select(
                attrs={
                    'required': 'True',
                    'class': 'custom-select',
                }
            ),

             'work_date': forms.DateInput(
                format='%d.%m.%y',
                attrs = {
                    'type': 'date',
                }
            ),
             'start_date': forms.DateInput(
                format='%d.%m.%y',
                attrs = {
                    'type': 'date',
                    'required': 'True',
                }
            ),
             'end_date': forms.DateInput(
                format='%d.%m.%y',
                attrs = {
                    'type': 'date',
                 
                }
            ),
             'substitute': forms.TextInput(
              
                attrs = {
                    'placeholder': "Proszę wpisać osobę (jeśli dotyczy)",
                }
            ),
             'days': forms.NumberInput(
              
                attrs = {
                    "type": "number",
                }
            ),
            }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date == None:
            raise forms.ValidationError('Proszę podać datę początkową urlopu.')
        return start_date

    def clean_end_date(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')
        if end_date==None:
            end_date = start_date
        if not end_date >= start_date:
            raise forms.ValidationError('Data końcowa nie może być wcześniejsza od daty początkowej.')
            # Nie działa: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1:
        if end_date > start_date: 
            if type=='WS':
                raise forms.ValidationError('Data końcowa nie powinna się różnić od daty początkowej w przypadku wolnego za pracującą sobotę lub niedzielę.')
        return end_date


    def clean_send_to_person(self):
        send_to_person = self.cleaned_data.get('send_to_person')
        if send_to_person == "" or send_to_person==None:
            raise forms.ValidationError('Proszę podać osobę, do której ma być wysłany wniosek.')
        return send_to_person

    def clean_work_date(self):
        work_date = self.cleaned_data.get('work_date')
        type = self.cleaned_data['type']
        if work_date == None and (type=='WN' or type=='WS'):
            raise forms.ValidationError('Proszę podać datę pracującej soboty, niedzieli lub święta.')
        return work_date

    def clean_days(self):
        days = self.cleaned_data.get('days')
        type = self.cleaned_data['type']
        if days == None and type=='W':
            raise forms.ValidationError('Proszę podać ilość dni (pełny etat) lub godzin (niepełny etat) urlopu.')
        return days


    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_show_labels = False 



class ReportForm(forms.Form):

    CHOICES = (("W", "urlop wypoczynkowy"), ("WS", "dni wolne za pracujące soboty oraz inne (WS, WN, DW)"), ("C", "zwolnienia lekarskie"),) 
      
    person = forms.ChoiceField(
        label = "Wybierz osobę",
        widget=forms.Select(attrs={'class':'selector'}),
        choices=(),
        )
    type=forms.ChoiceField(
        label = "Rodzaj",
        choices=CHOICES)  

    start_date = forms.DateField(
        label = "Od",
        widget=forms.SelectDateWidget(attrs={'style': 'width: 33%; display: inline-block;'}),
 
       )
    end_date = forms.DateField(
        label = "Do",
        widget=forms.SelectDateWidget(attrs={'style': 'width: 33%; display: inline-block;'}),
        initial = "2021-12-31",
    )
 

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        EXTRA_CHOICES = [('all_employees', 'Wszyscy pracownicy'),]
        choices = [(user.id, user) for user in User.objects.all().order_by('last_name', 'first_name')]
        choices.extend(EXTRA_CHOICES)
        self.fields['person'].choices = choices
