from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class EmployeeAdmin(UserAdmin):
    """Admin panel content for users"""

    list_display = (
        "last_name",
        "first_name",
        "position",
        "role",
        "workplace",
        "working_hours",
    )

    search_fields = ("last_name",)
    list_filter = (
        "role",
        "workplace",
    )
    readonly_fields = (
        "last_login",
        "password",
    )

    fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "password")}),
        (
            _("Basic Information"),
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "work_email",
                    "position",
                    "position_addinfo",
                    "role",
                    "manager",
                    "workplace",
                    "working_hours",
                    "contract_end",
                    "additional_info",
                ),
            },
        ),
        (
            _("Leave"),
            {"classes": ("wide",), "fields": ("current_leave", "annual_leave")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (None, {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


admin.site.unregister(Group)
admin.site.register(User, EmployeeAdmin)
