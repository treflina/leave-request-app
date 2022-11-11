from datetime import datetime, date
from crispy_forms.helper import FormHelper

from django.db.models.fields import DateField
from django import forms

from .models import Request, User


class RequestForm(forms.ModelForm):

    history_change_reason = forms.CharField(label="Powód wprowadzanych zmian", max_length=255, required=False)


    class Meta:
        model = Request
        fields = (
            "type",
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
            "duvet_day": forms.RadioSelect(choices=((False, "NIE"), (True, "TAK"),))
             }

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date == None:
            raise forms.ValidationError("Proszę podać datę początkową urlopu.")
        return start_date

    def clean_end_date(self):
        start_date = self.cleaned_data["start_date"]
        end_date = self.cleaned_data["end_date"]
        type = self.cleaned_data["type"]
        if not end_date:
            end_date = start_date
        if not end_date >= start_date:
            raise forms.ValidationError(
                "Data końcowa nie może być wcześniejsza od daty początkowej."
            )
        if (end_date != start_date) and (type == "WS" or type == "WN"):
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
        type = self.cleaned_data["type"]
        if work_date == None and (type == "WN" or type == "WS"):
            raise forms.ValidationError(
                "Proszę podać datę pracującej soboty, niedzieli lub święta."
            )
        return work_date

    def clean_days(self):
        days = self.cleaned_data.get("days")
        type = self.cleaned_data["type"]
        if days == None and type == "W":
            raise forms.ValidationError(
                "Proszę podać ilość dni (pełny etat) lub godzin (niepełny etat) urlopu."
            )
        return days

    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_show_labels = False

class UpdateRequestForm(RequestForm):
    history_change_reason = forms.CharField(label="Powód wprowadzanych zmian", max_length=255, required=False)
    class Meta:
        model = Request
        fields = (
            "type",
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
                choices=(
                        (False, "NIE"),
                        (True, "TAK"),
                        (None, "Nie dotyczy")
                        ))
             }



class ReportForm(forms.Form):

    now = datetime.now()

    CHOICES = (
        ("W", "urlop wypoczynkowy"),
        ("WS", "dni wolne za pracujące soboty oraz inne (WS, WN, DW)"),
        ("C", "zwolnienia lekarskie"),
    )

    person = forms.ChoiceField(
        label="Wybierz osobę",
        widget=forms.Select(attrs={"class": "selector"}),
        choices=(),
    )
    type = forms.ChoiceField(label="Rodzaj", choices=CHOICES)

    start_date = forms.DateField(
        label="Od",
        widget=forms.SelectDateWidget(
            attrs={"style": "width: 33%; display: inline-block;"},
            years=range(2021, 2035),
        ),
        initial=now.strftime("%Y") + "-01-01",
    )
    end_date = forms.DateField(
        label="Do",
        widget=forms.SelectDateWidget(
            attrs={"style": "width: 33%; display: inline-block;"},
            years=range(2022, 2035),
        ),
        initial=now.date()
        #
    )

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        EXTRA_CHOICES = [
            ("all_employees", "Wszyscy pracownicy"),
        ]
        choices = [
            (user.id, user)
            for user in User.objects.all().order_by("last_name", "first_name")
        ]
        choices.extend(EXTRA_CHOICES)
        self.fields["person"].choices = choices
