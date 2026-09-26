from django import forms

from .models import Sickleave
from applications.users.models import User


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return (
            obj.last_name + " " + obj.first_name + " " + obj.position_addinfo
        )


class SickleaveForm(forms.ModelForm):
    head = forms.BooleanField(label="dyrektora", required=False)
    manager = forms.BooleanField(label="kierownika", required=False)
    instructor = forms.BooleanField(label="instruktora", required=False)

    class Meta:
        model = Sickleave
        fields = (
            "employee",
            "leave_type",
            "issue_date",
            "doc_number",
            "start_date",
            "end_date",
            "additional_info",
        )

        labels = {
            "employee": ("Osoba"),
        }
        widgets = {
            "start_date": forms.DateInput(
                format="%d.%m.%y",
                attrs={
                    "type": "date",
                },
            ),
            "end_date": forms.DateInput(
                format="%d.%m.%y",
                attrs={
                    "type": "date",
                },
            ),
            "issue_date": forms.DateInput(
                format="%d.%m.%y",
                attrs={
                    "type": "date",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super(SickleaveForm, self).__init__(*args, **kwargs)

        self.fields["head"].initial = True
        self.fields["manager"].initial = True
        self.fields["instructor"].initial = True
        self.fields["employee"] = UserModelChoiceField(
            label="Osoba", queryset=User.objects.all()
        )
        for field_name, field in self.fields.items():
            if field.widget.input_type == "checkbox":
                field.widget.attrs["class"] = (
                    "h-4 w-4 rounded border-slate-300 text-[#28a745] "
                    "focus:ring-[#28a745]"
                )
            else:
                field.widget.attrs["class"] = (
                    "mt-1 w-full rounded-lg border border-slate-300 bg-slate-50/50 "
                    "px-3 py-2 text-sm text-slate-800 focus:border-[#28a745] "
                    "focus:bg-white focus:outline-none focus:ring-2 "
                    "focus:ring-[#28a745]/20"
                )
            if field_name in self.errors:
                field.widget.attrs.update(
                    {
                        "aria-invalid": "true",
                        "aria-describedby": f"id_{field_name}-errors",
                    }
                )
