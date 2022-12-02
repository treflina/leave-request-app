from django.contrib import admin
from django.utils.html import format_html

from simple_history.admin import SimpleHistoryAdmin
from .models import Request


class RequestsAdmin(SimpleHistoryAdmin):
    """Admin panel content for requests."""

    list_display = (
        "author",
        "work_date",
        "start_date",
        "days",
        "status",
        "send_to_person",
    )
    search_fields = ("author__last_name", "author__first_name")
    list_filter = ("leave_type",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "author",
                    "created",
                    "leave_type",
                    "start_date",
                    "end_date",
                    "work_date",
                    "days",
                    "duvet_day",
                    "substitute",
                    "status",
                    "send_to_person",
                    "signed_by",
                )
            },
        ),
        (
            "Uzasadnienie wprowadzonych zmian we wniosku",
            {"fields": ("attachment",)},
        ),
    )
    readonly_fields = (
        "author",
        "created",
        "signed_by",
    )

    history_list_display = ["changed_fields", "list_changes"]

    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return delta.changed_fields
        return None

    def list_changes(self, obj):
        fields = ""
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)

            for change in delta.changes:
                fields += str(
                    "<strong>{}</strong> changed from <span style='background-color:#ffb5ad'>{}</span> to <span style='background-color:#b3f7ab'>{}</span> . <br/>".format(
                        change.field, change.old, change.new
                    )
                )
            return format_html(fields)
        return None


admin.site.register(Request, RequestsAdmin)
