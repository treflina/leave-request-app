from django.contrib import admin
from django.contrib.auth.models import Group


from .models import User


class EmployeeAdmin(admin.ModelAdmin):
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


admin.site.unregister(Group)
admin.site.register(User, EmployeeAdmin)
