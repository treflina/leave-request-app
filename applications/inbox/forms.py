from django import forms
from django.contrib.auth import get_user_model

from .models import Message


User = get_user_model()


class MessageForm(forms.ModelForm):

    class Meta:
        model = Message
        fields = [
            "msg_title",
            "msg_content",
            "employees",
        ]

        widgets = {
            "msg_title": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-lg border border-slate-300 "
                        "bg-white px-4 py-2.5 text-sm text-slate-900 "
                        "placeholder:text-slate-400 "
                        "focus:border-green-700 "
                        "focus:outline-none "
                        "focus-visible:ring-2 "
                        "focus-visible:ring-green-700 "
                        "focus-visible:ring-offset-2 "
                        "focus-visible:ring-offset-white"
                    ),
                    "placeholder": "Tytuł wiadomości",
                    "autocomplete": "off",
                }
            ),

            "msg_content": forms.Textarea(
                attrs={
                    "class": (
                        "w-full rounded-lg border border-slate-300 "
                        "bg-white px-4 py-2.5 text-sm text-slate-900 "
                        "placeholder:text-slate-400 "
                        "focus:border-green-700 "
                        "focus:outline-none "
                        "focus-visible:ring-2 "
                        "focus-visible:ring-green-700 "
                        "focus-visible:ring-offset-2 "
                        "focus-visible:ring-offset-white"
                    ),
                    "rows": 8,
                    "placeholder": "Treść wiadomości",
                }
            ),

            "employees": forms.CheckboxSelectMultiple(
                attrs={
                    "aria-describedby": "employees-help",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["employees"].queryset = (
            User.objects
            .filter(is_active=True)
            .order_by("last_name", "first_name")
        )

        for field_name in ("msg_title", "msg_content"):
            field = self.fields[field_name]

            if self.errors.get(field_name):
                field.widget.attrs.update({
                    "aria-invalid": "true",
                    "aria-describedby": (
                        f"{field_name}-error"
                    ),
                })

        for employee in self.fields["employees"].queryset:
            label = (
                f"{employee.first_name} "
                f"{employee.last_name}"
            ).strip()

            if not label:
                label = employee.username

            self.fields["employees"].widget.attrs.update({
                "aria-label": "Wybierz pracowników",
            })