from io import BytesIO
from datetime import date

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer,
    Paragraph,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle

from django.db.models import Q
from django.http import FileResponse

from applications.requests.models import Request
from applications.sickleaves.models import Sickleave
from applications.users.models import User


pdfmetrics.registerFont(TTFont("signika", "./static/fonts/signika.ttf"))
pdfmetrics.registerFont(TTFont("signika-bold", "./static/fonts/signika-bold.ttf"))

pdfmetrics.registerFontFamily(
    "signika",
    normal="signika",
    bold="signika-bold",
)


def create_pdf_sheet(data, fileName, title, start_date, end_date):
    if title == "Wykaz zwolnień lekarskich":
        pagesize = A4
        table_font_size = 10
    else:
        pagesize = landscape(A4)
        table_font_size = 12

    pdf = SimpleDocTemplate(
        fileName,
        pagesize=pagesize,
        rightMargin=50,
        leftMargin=50,
        topMargin=30,
        bottomMargin=30,
    )
    style = ParagraphStyle(
        name="Title",
        fontName="signika",
        fontSize=12,
        alignment=TA_CENTER,
    )
    style1 = ParagraphStyle(
        name="footer",
        fontName="signika",
        fontSize=10,
        alignment=TA_CENTER,
    )

    elems = []
    for person in data:
        if len(person["table_data"]) > 1:
            table = Table(person["table_data"])

            elems.append(
                Paragraph(
                    f"{title} w okresie od {start_date.strftime('%d-%m-%Y')} do {end_date.strftime('%d-%m-%Y')}",
                    style=style,
                )
            )
            elems.append(Spacer(1, 16))
            if person["position"] != "":
                elems.append(
                    Paragraph(
                        f"<b>{person['name']}</b> ({person['position']})",
                        style=style,
                    )
                )
                elems.append(Spacer(1, 20))
            elems.append(table)
            style_table = TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "signika"),
                    ("FONTSIZE", (0, 0), (-1, -1), table_font_size),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (4, 1), (5, -1), "CENTER"),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ]
            )
            table.setStyle(style_table)
            elems.append(Spacer(1, 20))
            elems.append(
                Paragraph(
                    """Miejska Biblioteka Publiczna im. Jana Pawła II w Opolu. Wygenerowano z Pracownik MBP""",
                    style=style1,
                )
            )
            elems.append(PageBreak())

    pdf.build(elems)


def create_pdf_report(person, start_date, end_date, leave_type, attachment):
    pdf_buffer = BytesIO()

    annualleave_header = [
        [
            "Lp.",
            "Złożony",
            "Nazwisko i imię",
            "Od",
            "Do",
            "Dni/godz.",
            "Status",
            "Podpisany przez:",
        ]
    ]
    othertypeleave_header = [
        [
            "Lp.",
            "Złożony",
            "Nazwisko i imię",
            "Na dzień",
            "Rodzaj",
            "Za pracę dnia",
            "Status",
            "Podpisany przez:",
        ]
    ]
    sickleaves_header = [
        [
            "Lp.",
            "Wystawiony",
            "Nr dokumentu",
            "Nazwisko i imię",
            "Rodzaj",
            "Od",
            "Do",
            "Inne",
        ]
    ]

    table_data_employee = []

    def create_data_dict(name, position, employee_data):
        """helper function to create dictionary with requested data about chosen employee"""
        data_employee = {}
        data_employee["name"] = name
        data_employee["position"] = position
        data_employee["table_data"] = employee_data
        table_data_employee.append(data_employee)
        return table_data_employee

    if leave_type == "W":
        """report about annual leave"""

        title = "Wykaz wniosków urlopowych"

        for p in person:
            x = 1
            employee_data = []
            employee_data += annualleave_header
            if p == "all_employees":
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
                requests_data = Request.objects.filter(
                    Q(leave_type="W")
                    & (
                        Q(start_date__range=(start_date, end_date))
                        | Q(end_date__range=(start_date, end_date))
                    )
                ).order_by("author", "created")

            else:
                employee = User.objects.get(id=p)
                name = f"{employee.last_name} {employee.first_name}"
                position = employee.position
                requests_data = Request.objects.filter(
                    Q(leave_type="W")
                    & Q(author__id=employee.id)
                    & (
                        Q(start_date__range=(start_date, end_date))
                        | Q(end_date__range=(start_date, end_date))
                    )
                ).order_by("created")

            for item in requests_data:
                created_newformat = item.created.strftime("%d-%m-%y")
                employee_repr = f"{item.author.last_name} {item.author.first_name} {item.author.position_addinfo}"

                data = [
                    x,
                    created_newformat,
                    employee_repr,
                    item.start_date.strftime("%d-%m-%y"),
                    item.end_date.strftime("%d-%m-%y"),
                    item.days,
                    item.status,
                    item.signed_by,
                ]
                employee_data.append(data)
                x += 1
            create_data_dict(name, position, employee_data)

        create_pdf_sheet(table_data_employee, pdf_buffer, title, start_date, end_date)
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer,
            as_attachment=attachment,
            filename=f"wykaz urlopów {employee}.pdf",
        )

    elif leave_type == "WS":
        """report about other type leaves"""

        title = "Wykaz wniosków o dni wolne za pracujące soboty (niedziele, święta)"

        for p in person:
            x = 1
            employee_data = []
            employee_data += othertypeleave_header
            if p == "all_employees":
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
                requests_data = (
                    Request.objects.filter(
                        ~Q(leave_type="W") & Q(start_date__range=(start_date, end_date))
                    )
                    .order_by("author", "created")
                    .all()
                )
            else:
                employee = User.objects.get(id=p)
                name = f"{employee.last_name} {employee.first_name}"
                position = employee.position
                requests_data = (
                    Request.objects.filter(
                        ~Q(leave_type="W")
                        & Q(author__id=employee.id)
                        & Q(start_date__range=(start_date, end_date))
                    )
                    .order_by("created")
                    .all()
                )

            for item in requests_data:
                created_newformat = item.created.strftime("%d-%m-%y")
                employee_repr = f"{item.author.last_name} {item.author.first_name} {item.author.position_addinfo}"

                if not isinstance(item.work_date, date):
                    work_date = ""
                else:
                    work_date = item.work_date.strftime("%d-%m-%y")

                data = [
                    x,
                    created_newformat,
                    employee_repr,
                    item.start_date.strftime("%d-%m-%y"),
                    item.leave_type,
                    work_date,
                    item.status,
                    item.signed_by,
                ]
                employee_data.append(data)
                x += 1
            create_data_dict(name, position, employee_data)

        create_pdf_sheet(table_data_employee, pdf_buffer, title, start_date, end_date)
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer,
            as_attachment=attachment,
            filename=f"wykaz dni wolne {employee}.pdf",
        )

    if leave_type == "C":
        """report about sick leaves"""

        for p in person:
            x = 1
            employee_data = []
            employee_data += sickleaves_header
            if p == "all_employees":
                name = ""
                position = ""
                employee = "- wszyscy pracownicy"
                sickleaves_data = (
                    Sickleave.objects.filter(
                        Q(start_date__gte=start_date) & Q(start_date__lte=end_date)
                    )
                    .order_by("employee__last_name", "start_date")
                    .all()
                )

            else:
                employee = User.objects.get(id=p)
                name = employee.last_name + " " + employee.first_name
                position = employee.position
                sickleaves_data = (
                    Sickleave.objects.filter(
                        Q(employee__id=employee.id)
                        & Q(start_date__gte=start_date)
                        & Q(start_date__lte=end_date)
                    )
                    .order_by("start_date")
                    .all()
                )

            for item in sickleaves_data:
                employee_repr = f"{item.employee.last_name} {item.employee.first_name} {item.employee.position_addinfo}"
                additional_info = (
                    item.additional_info
                    if len(item.additional_info) < 25
                    else item.additional_info[:24] + "..."
                )
                data = [
                    x,
                    item.issue_date.strftime("%d-%m-%y"),
                    item.doc_number,
                    employee_repr,
                    item.leave_type,
                    item.start_date.strftime("%d-%m-%y"),
                    item.end_date.strftime("%d-%m-%y"),
                    additional_info,
                ]

                employee_data.append(data)
                x += 1
            create_data_dict(name, position, employee_data)

        title = "Wykaz zwolnień lekarskich"
        create_pdf_sheet(table_data_employee, pdf_buffer, title, start_date, end_date)
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer, as_attachment=attachment, filename=f"chorobowe {employee}.pdf"
        )
