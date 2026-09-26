from django import forms
from django.contrib.auth import authenticate
from django.db.models import Q

from .models import User


class UserRegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Hasło",
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Hasło"}),
    )
    password2 = forms.CharField(
        label="Powtórz hasło",
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Powtórz hasło"}),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "work_email",
            "first_name",
            "last_name",
            "position",
            "position_addinfo",
            "workplace",
            "role",
            "manager",
            "working_hours",
            "annual_leave",
            "current_leave",
            "contract_end",
            "additional_info",
            "is_active",
            "is_staff",
            "email_notifications"
        )
        widgets = {
            "contract_end": forms.DateInput(
                format="%d.%m.%Y",
                attrs={
                    "type": "date",
                },
            ),
        }

    def clean_password2(self):
        if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
            self.add_error("password2", "Wprowadzone hasła nie są identyczne.")

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields["manager"] = forms.ModelChoiceField(
            queryset=User.objects.filter(
                ~Q(role="P") & Q(is_active=True)
                ).order_by(
                "last_name"
            ),
            required=False,
            label="Przełożony",
        )
        for field in self.fields.values():
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


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Nazwa użytkownika",
        required=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nazwa użytkownika",
            }
        ),
    )

    password = forms.CharField(
        label="Hasło",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Hasło",
            }
        ),
    )

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if not authenticate(username=username, password=password):
            raise forms.ValidationError(
                "Dane podane do logowania nie są prawidłowe."
                )

        return cleaned_data


class UpdatePasswordForm(forms.Form):
    password1 = forms.CharField(
        label="Dotychczasowe hasło",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Dotychczasowe hasło",
            }
        ),
    )
    password2 = forms.CharField(
        label="Nowe hasło",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Nowe hasło",
            }
        ),
    )

    password3 = forms.CharField(
        label="Powtórz nowe hasło",
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Powtórz nowe hasło",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "mt-1 w-full rounded-lg border border-slate-300 bg-white "
                "px-3 py-2 text-sm text-slate-900 focus:border-[#28a745] "
                "focus:outline-none focus:ring-2 focus:ring-[#28a745]/30"
            )
