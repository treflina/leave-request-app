from datetime import date

from django import forms

from applications.users.models import User


class ReportForm(forms.Form):
    TYPE_CHOICES = (
        ("W", "urlop wypoczynkowy"),
        ("WS", "dni wolne za pracujące soboty oraz inne (WS, WN, DW)"),
        ("C", "zwolnienia lekarskie"),
    )

    ATTACHMENT_CHOICES = (
        (True, "Pobierz"),
        (False, "Wyświetl"),
    )

    REPORT_FORMAT_CHOICES = (
        ("pdf", "PDF"),
        ("txt", "TXT"),
        ("certificate", "do świadectwa pracy"),
    )

    CONTROL_CLASSES = (
        "mt-1 block w-full rounded-lg border border-slate-300 bg-white "
        "px-3 py-2 text-sm text-slate-700 shadow-sm transition-colors "
        "focus:border-green-600 focus:outline-none "
        "focus:ring-2 focus:ring-green-600/20"
    )

    person = forms.MultipleChoiceField(
        label="Wybierz osobę",
        choices=(),
        widget=forms.SelectMultiple(
            attrs={
                "class": CONTROL_CLASSES,
                "size": "8",
            }
        ),
    )

    leave_type = forms.ChoiceField(
        label="Rodzaj",
        choices=TYPE_CHOICES,
        initial="W",
        widget=forms.Select(
            attrs={"class": CONTROL_CLASSES},
        ),
    )

    report_format = forms.ChoiceField(
        label="Format raportu",
        choices=REPORT_FORMAT_CHOICES,
        initial="pdf",
        widget=forms.RadioSelect(),
    )

    start_date = forms.DateField(
        label="Od",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": CONTROL_CLASSES,
            }
        ),
    )

    end_date = forms.DateField(
        label="Do",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": CONTROL_CLASSES,
            }
        ),
    )

    attachment = forms.BooleanField(
        label="Pobieranie raportu",
        required=False,
        widget=forms.RadioSelect(
            choices=ATTACHMENT_CHOICES,
        ),
        initial=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = date.today()

        self.fields["start_date"].initial = date(today.year, 1, 1)
        self.fields["end_date"].initial = today

        self.fields["person"].choices = [
            ("all_employees", "Wszyscy pracownicy - zestawienie"),
            *(
                (user.id, user)
                for user in User.objects.order_by(
                    "last_name",
                    "first_name",
                )
            ),
        ]

    def clean_person(self):
        person = self.cleaned_data["person"]

        if not person:
            raise forms.ValidationError(
                "Proszę wybrać co najmniej jedną osobę."
            )

        return person

    def clean(self):
        cleaned_data = super().clean()

        leave_type = cleaned_data.get("leave_type")
        report_format = cleaned_data.get("report_format")

        if report_format == "certificate" and leave_type != "C":
            self.add_error(
                "report_format",
                "Format „do świadectwa pracy” jest dostępny tylko dla zwolnień lekarskich.",
            )

        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            self.add_error(
                None,
                "Data początkowa nie może być późniejsza niż data końcowa.",
            )

        return cleaned_data
