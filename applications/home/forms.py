from datetime import datetime
# from django.db.models.fields import DateField
from django import forms
from applications.users.models import User

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
    leave_type = forms.ChoiceField(label="Rodzaj", choices=CHOICES)

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