from datetime import date

from crispy_forms.helper import FormHelper
from django import forms

from .models import Request


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
                    "required": True,
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
        td = date.today().year
        start_date = self.cleaned_data.get("start_date")
        if start_date is None:
            raise forms.ValidationError("Proszę podać datę początkową urlopu.")
        if start_date.year < td - 1 or start_date.year > td + 1:
            raise forms.ValidationError(
                "Proszę podać prawidłowy rok w formacie 'RRRR'."
            )
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        if end_date is None:
            start_date = self.cleaned_data.get("start_date")
            if start_date:
                end_date = start_date
        return end_date

    def clean_send_to_person(self):
        send_to_person = self.cleaned_data.get("send_to_person")
        if not send_to_person:
            raise forms.ValidationError(
                "Proszę podać osobę, do której ma być wysłany wniosek."
            )
        return send_to_person

    def clean_work_date(self):
        work_date = self.cleaned_data.get("work_date")
        leave_type = self.cleaned_data.get("leave_type")
        if work_date is None and leave_type in ["WN", "WS"]:
            raise forms.ValidationError(
                "Proszę podać datę pracującej soboty, niedzieli lub święta."
            )
        return work_date

    def clean_days(self):
        days = self.cleaned_data.get("days")
        leave_type = self.cleaned_data.get("leave_type")
        if leave_type == "W":
            if days is None or days <= 0:
                raise forms.ValidationError(
                    """Proszę podać prawidłową ilość dni (pełny etat)
                    lub godzin (niepełny etat) urlopu."""
                )
        return days

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        leave_type = cleaned_data.get("leave_type")

        if start_date is not None and end_date is not None:
            if end_date < start_date:
                raise forms.ValidationError(
                    """Data końcowa nie może być wcześniejsza
                    od daty początkowej."""
                )
            if (end_date != start_date) and (leave_type in ["WS", "WN"]):
                raise forms.ValidationError(
                    """Data końcowa nie powinna się różnić od daty początkowej
                    w przypadku wolnego za pracującą sobotę lub niedzielę."""
                )

        if leave_type in ["WS", "WN", "DW"]:
            cleaned_data["days"] = 0

        if leave_type not in ["WS", "WN"]:
            cleaned_data["work_date"] = None

        if leave_type != "W":
            cleaned_data["duvet_day"] = None

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(RequestForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False


class UpdateRequestForm(RequestForm):

    class Meta(RequestForm.Meta):
        fields = RequestForm.Meta.fields + ("attachment", "status")
        widgets = {
            **RequestForm.Meta.widgets,
            "attachment": forms.ClearableFileInput(
                attrs={"required": False}
            ),
            "duvet_day": forms.RadioSelect(
                choices=((False, "NIE"), (True, "TAK"), (None, "Nie dotyczy"))
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attachment"].widget.clear_checkbox_label = "Usuń"
        self.fields["attachment"].widget.initial_text = "Załączono"
        self.fields["attachment"].widget.input_text = "Zmień"
