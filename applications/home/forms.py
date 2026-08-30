from datetime import datetime
from django import forms
from applications.users.models import User


class ReportForm(forms.Form):

    now = datetime.now()

    TYPE_CHOICES = (
        ("W", "urlop wypoczynkowy"),
        ("WS", "dni wolne za pracujące soboty oraz inne (WS, WN, DW)"),
        ("C", "zwolnienia lekarskie"),
    )

    ATTACHMENT_CHOICES = ((True, "Pobierz"), (False, "Wyświetl"))
    REPORT_FORMAT_CHOICES = (
        ("pdf", "PDF"),
        ("txt", "TXT"),
        ("certificate", "do świadectwa pracy"),
    )

    person = forms.MultipleChoiceField(
        label="Wybierz osobę",
        widget=forms.SelectMultiple(attrs={"class": "selector"}),
        choices=(),
    )
    leave_type = forms.ChoiceField(
        label="Rodzaj",
        choices=TYPE_CHOICES,
        initial="W",
    )
    report_format = forms.ChoiceField(
        label="Format raportu",
        choices=REPORT_FORMAT_CHOICES,
        initial="pdf",
        widget=forms.RadioSelect,
    )

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
        initial=datetime.now().date(),
    )

    attachment = forms.BooleanField(
        label="",
        required=False,
        widget=forms.RadioSelect(choices=ATTACHMENT_CHOICES),
        initial=True,
    )

    def clean_person(self):
        person = self.cleaned_data.get("person")
        if not person:
            raise forms.ValidationError(
                "Proszę wybrać co najmniej jedną osobę."
            )
        return person

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        EXTRA_CHOICES = [
            ("all_employees", "Wszyscy pracownicy - zestawienie"),
        ]
        choices = [
            (user.id, user)
            for user in User.objects.all().order_by("last_name", "first_name")
        ]
        choices = EXTRA_CHOICES + choices
        self.fields["person"].choices = choices
