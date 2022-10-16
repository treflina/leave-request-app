from django.contrib import admin
from .models import Sickleave


class SickleavesAdmin(admin.ModelAdmin):
    """Sick leave admin panel content."""

    list_display = (
        "employee",
        "type",
        "issue_date",
        "doc_number",
        "start_date",
        "end_date",
        "additional_info",
    )
    search_fields = ("employee__last_name", "employee__first_name")


admin.site.register(Sickleave, SickleavesAdmin)
