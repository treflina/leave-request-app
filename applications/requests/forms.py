from datetime import datetime, date
from crispy_forms.helper import FormHelper

from django.db.models.fields import DateField
from django import forms

from .models import Request, User


class RequestForm(forms.ModelForm):

    history_change_reason = forms.CharField(
        label="Powód wprowadzanych zmian", max_length=255, required=False
    )

    class Meta:
        model = Request
        fields = (
            "leave_type",
            "start_date",
            "end_date",
            "days",
            "work_date",
            "substitute",
            "send_to_person",
            "duvet_day",
        )
        widgets = {
            "send_to_person": forms.Select(
                attrs={
                    "required": "True",
                    "class": "custom-select",
                }
            ),
            "work_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "start_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "required": "True",
                },
            ),
            "end_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "substitute": forms.TextInput(
                attrs={
                    "placeholder": "Proszę wpisać osobę (jeśli dotyczy)",
                }
            ),
            "days": forms.NumberInput(
                attrs={
                    "type": "number",
                }
            ),
            "duvet_day": forms.RadioSelect(
                choices=(
                    (False, "NIE"),
                    (True, "TAK"),
                )
            ),
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date == None:
            raise forms.ValidationError("Proszę podać datę początkową urlopu.")
        return start_date

    def clean_end_date(self):
        start_date = self.cleaned_data["start_date"]
        end_date = self.cleaned_data["end_date"]
        leave_type = self.cleaned_data["leave_type"]
        if not end_date:
            end_date = start_date
        if not end_date >= start_date:
            raise forms.ValidationError(
                "Data końcowa nie może być wcześniejsza od daty początkowej."
            )
        if (end_date != start_date) and (leave_type == "WS" or leave_type == "WN"):
            raise forms.ValidationError(
                "Data końcowa nie powinna się różnić od daty początkowej w przypadku wolnego za pracującą sobotę lub niedzielę."
            )
        return end_date

    def clean_send_to_person(self):
        send_to_person = self.cleaned_data.get("send_to_person")
        if send_to_person == "" or send_to_person == None:
            raise forms.ValidationError(
                "Proszę podać osobę, do której ma być wysłany wniosek."
            )
        return send_to_person

    def clean_work_date(self):
        work_date = self.cleaned_data.get("work_date")
        leave_type = self.cleaned_data["leave_type"]
        if work_date == None and (leave_type == "WN" or leave_type == "WS"):
            raise forms.ValidationError(
                "Proszę podać datę pracującej soboty, niedzieli lub święta."
            )
        return work_date

    def clean_days(self):
        days = self.cleaned_data.get("days")
        leave_type = self.cleaned_data["leave_type"]
        if days == None and leave_type == "W":
            raise forms.ValidationError(
                "Proszę podać ilość dni (pełny etat) lub godzin (niepełny etat) urlopu."
            )
        return days

    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_show_labels = False


class UpdateRequestForm(RequestForm):
    history_change_reason = forms.CharField(
        label="Powód wprowadzanych zmian", max_length=255, required=False
    )

    class Meta:
        model = Request
        fields = (
            "leave_type",
            "start_date",
            "end_date",
            "days",
            "work_date",
            "substitute",
            "send_to_person",
            "attachment",
            "status",
            "duvet_day",
        )
        widgets = {
            "send_to_person": forms.Select(
                attrs={
                    "required": "True",
                    "class": "custom-select",
                }
            ),
            "work_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "start_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "required": "True",
                },
            ),
            "end_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "substitute": forms.TextInput(
                attrs={
                    "placeholder": "Proszę wpisać osobę (jeśli dotyczy)",
                }
            ),
            "days": forms.NumberInput(
                attrs={
                    "type": "number",
                }
            ),
            "attachment": forms.ClearableFileInput(
                attrs={
                    "type": "file",
                    "required": False,
                }
            ),
            "duvet_day": forms.RadioSelect(
                choices=((False, "NIE"), (True, "TAK"), (None, "Nie dotyczy"))
            ),
        }
