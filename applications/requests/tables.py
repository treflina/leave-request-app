import django_tables2 as tables

from django_tables2 import TemplateColumn

from .models import Request


class BaseRequestsTable(tables.Table):
    row_number = tables.Column(
        verbose_name="Lp.",
        orderable=False,
    )

    created = tables.DateColumn(
        verbose_name="Z dnia",
        format="d.m.y",
        orderable=True,
        attrs={
            "th": {
                "class": (
                    "px-4 py-3.5 text-left text-xs font-semibold "
                    "uppercase tracking-wider whitespace-nowrap"
                )
            },
        },
    )

    author = tables.Column(
        verbose_name="Nazwisko i imię",
        accessor="author.last_name",
        orderable=True,
        attrs={
            "th": {
                "class": (
                    "px-4 py-3.5 text-left text-xs font-semibold "
                    "uppercase tracking-wider whitespace-nowrap"
                )
            },
        },
    )

    period = tables.Column(
        empty_values=(),
        verbose_name="Okres",
        orderable=True,
        order_by=("start_date", "end_date"),
        attrs={
            "th": {
                "class": (
                    "px-4 py-3.5 text-left text-xs font-semibold "
                    "uppercase tracking-wider whitespace-nowrap"
                )
            },
        },
    )

    leave_type_display = tables.Column(
        empty_values=(),
        verbose_name="Rodzaj",
        orderable=False,
        order_by="leave_type",
    )

    days = tables.Column(
        verbose_name="L. dni*",
        orderable=False,
    )

    substitute = tables.Column(
        verbose_name="Zastępuje",
        orderable=False,
    )

    def render_author(self, value, record):
        full_name = f"{record.author.last_name} {record.author.first_name}"

        if record.author.position_addinfo:
            full_name += f" ({record.author.position_addinfo})"

        return full_name

    def render_period(self, record):
        start = (
            record.start_date.strftime("%d.%m.%y")
            if record.start_date
            else ""
        )
        end = (
            record.end_date.strftime("%d.%m.%y")
            if record.end_date
            else ""
        )

        if not start:
            return "-"

        if start == end or not end:
            return start

        return f"{start} - {end}"

    def render_leave_type_display(self, record):
        text = record.leave_type or ""

        if record.work_date:
            text += f" za {record.work_date.strftime('%d.%m.%y')}"

        if record.duvet_day:
            text += " (nż***)"

        return text

    def render_days(self, value, record):
        if value and value > 0:
            return value

        return "-"

    def render_substitute(self, value, record):
        return value if value else "-"

    class Meta:
        model = Request
        template_name = "tables/table_htmx.html"
        empty_text = "Brak wniosków spełniających kryteria wyszukiwania."
        fields = (
            "row_number",
            "created",
            "author",
            "period",
            "leave_type_display",
            "days",
            "substitute",
        )
        attrs = {
            "class": "table-auto w-full",
        }


class RequestsTable(BaseRequestsTable):
    status_display = TemplateColumn(
        template_name="requests/includes/request_status_column.html",
        verbose_name="Status",
        orderable=False,
        order_by="status",
    )

    class Meta(BaseRequestsTable.Meta):
        fields = BaseRequestsTable.Meta.fields + (
            "status_display",
        )


class HRRequestsTable(BaseRequestsTable):
    status_display = TemplateColumn(
        template_name="requests/includes/hr_status_column.html",
        verbose_name="Status",
        orderable=False,
        order_by="status",
    )

    actions = TemplateColumn(
        template_name="requests/includes/hr_actions_column.html",
        verbose_name="",
        orderable=False,
    )

    class Meta(BaseRequestsTable.Meta):
        fields = BaseRequestsTable.Meta.fields + (
            "status_display",
            "actions",
        )