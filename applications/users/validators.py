from django.contrib.auth.password_validation import (
    MinimumLengthValidator as BaseMinimumLengthValidator,
)


class MinimumLengthValidator(BaseMinimumLengthValidator):
    """Same check as Django's validator, but with a Polish message.

    Django's own translation for this message doesn't apply: its
    get_error_message() substitutes min_length into the string before
    calling ngettext(), so the lookup never matches the catalog's
    "%d"-placeholder msgid and it always falls back to English.
    """

    def get_error_message(self):
        return (
            f"To hasło jest za krótkie. Musi zawierać co najmniej "
            f"{self.min_length} znaków."
        )

    def get_help_text(self):
        return f"Hasło musi zawierać co najmniej {self.min_length} znaków."
