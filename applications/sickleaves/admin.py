from django.contrib import admin
from .models import (
    Sickleave,
    EZLAReportDownload,
    EZLAReportGeneration
)


class SickleavesAdmin(admin.ModelAdmin):
    """Sick leave admin panel content."""

    list_display = (
        "employee",
        "leave_type",
        "issue_date",
        "doc_number",
        "start_date",
        "end_date",
        "additional_info",
    )
    search_fields = ("employee__last_name", "employee__first_name")


admin.site.register(Sickleave, SickleavesAdmin)
admin.site.register(EZLAReportDownload)
admin.site.register(EZLAReportGeneration)
