from io import BytesIO
from datetime import datetime, date

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle

from django.db.models import Q
from django.http import FileResponse

from applications.requests.models import Request
from applications.sickleaves.models import Sickleave
from applications.users.models import User



pdfmetrics.registerFont(TTFont("TNR", "./static/fonts/signikan.ttf"))


def create_pdf_sheet(data, fileName, title, start_date, end_date, person, position):

    pdf = SimpleDocTemplate(
        fileName,
        pagesize=landscape(A4),
        rightMargin=50,
        leftMargin=50,
        topMargin=30,
        bottomMargin=30,
    )

    table = Table(data)
    elems = []
    style = ParagraphStyle(
        name="Title",
        fontName="TNR",
        fontSize=12,
        alignment=TA_CENTER,
    )
    style1 = ParagraphStyle(
        name="footer",
        fontName="TNR",
        fontSize=10,
        alignment=TA_CENTER,
    )
    elems.append(
        Paragraph(f"{title} w okresie od {start_date.strftime('%d-%m-%Y')} do {end_date.strftime('%d-%m-%Y')}", style=style)
    )
    elems.append(Spacer(1, 16))
    if position != "":
        elems.append(Paragraph(f"{person} (stanowisko: {position})", style=style))
        elems.append(Spacer(1, 20))
    elems.append(table)
    style_table = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "TNR"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (4, 1), (5, -1), 'CENTER'),
            ("ALIGN", (1, 0), (1, -1), 'CENTER'),
            ("ALIGN", (0, 0), (0, -1), 'RIGHT'),
        ]
    )
    table.setStyle(style_table)
    elems.append(Spacer(1, 20))
    elems.append(Paragraph("""Miejska Biblioteka Publiczna im. Jana Pawła II w Opolu. Wygenerowano z Pracownik MBP""", style=style1))

    pdf.build(elems)


def create_pdf_report(person, start_date, end_date, leave_type):
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

    name = ""
    position = ""
    employee = "- wszyscy pracownicy"
    x = 1

    if leave_type == "W":
        """report about annual leave"""

        if person == "all_employees":
            requests_data = Request.objects.filter(
                Q(leave_type="W")
                & (
                    Q(start_date__range=(start_date, end_date))
                    | Q(end_date__range=(start_date, end_date))
                )
            ).order_by("author","created")

        else:
            employee = User.objects.get(id=person)
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
            created_newformat = item.created.strftime('%d-%m-%y')
            employee_repr = f"{item.author.last_name} {item.author.first_name} {item.author.position_addinfo}"

            data = [
                x,
                created_newformat,
                employee_repr,
                item.start_date.strftime('%d-%m-%y'),
                item.end_date.strftime('%d-%m-%y'),
                item.days,
                item.status,
                item.signed_by,
            ]
            annualleave_header.append(data)
            x += 1
        title = "Wykaz wniosków urlopowych"
        create_pdf_sheet(
            annualleave_header, pdf_buffer, title, start_date, end_date, name, position
        )
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer, as_attachment=True, filename=f"wykaz urlopów {employee}.pdf"
        )

    elif leave_type == "WS":
        """report about other type leaves"""

        if person == "all_employees":
            requests_data = (
                Request.objects.filter(
                    ~Q(leave_type="W") & Q(start_date__range=(start_date, end_date))
                )
                .order_by("author","created")
                .all()
            )
        else:
            employee = User.objects.get(id=person)
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
            created_newformat = item.created.strftime('%d-%m-%y')
            employee_repr = f"{item.author.last_name} {item.author.first_name} {item.author.position_addinfo}"

            if not isinstance(item.work_date, date):
                work_date =""
            else:
                work_date = item.work_date.strftime('%d-%m-%y')

            data1 = [
                x,
                created_newformat,
                employee_repr,
                item.start_date.strftime('%d-%m-%y'),
                item.leave_type,
                work_date,
                item.status,
                item.signed_by,
            ]
            othertypeleave_header.append(data1)
            x += 1

        title = "Wykaz wniosków o dni wolne za pracujące soboty (niedziele, święta)"
        create_pdf_sheet(
            othertypeleave_header,
            pdf_buffer,
            title,
            start_date,
            end_date,
            name,
            position,
        )
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer, as_attachment=True, filename=f"wykaz dni wolne {employee}.pdf"
        )

    if leave_type == "C":
        """report about sick leaves"""

        if person == "all_employees":
            sickleaves_data = (
                Sickleave.objects.filter(
                    Q(start_date__gte=start_date) & Q(start_date__lte=end_date)
                )
                .order_by("employee__last_name", "start_date")
                .all()
            )

        else:
            employee = User.objects.get(id=person)
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
            data2 = [
                x,
                item.issue_date.strftime('%d-%m-%y'),
                item.doc_number,
                employee_repr,
                item.leave_type,
                item.start_date.strftime('%d-%m-%y'),
                item.end_date.strftime('%d-%m-%y'),
                item.additional_info,
            ]
            sickleaves_header.append(data2)
            x += 1
        title = "Wykaz zwolnień lekarskich"
        create_pdf_sheet(
            sickleaves_header, pdf_buffer, title, start_date, end_date, name, position
        )
        pdf_buffer.seek(0)
        return FileResponse(
            pdf_buffer, as_attachment=True, filename=f"chorobowe {employee}.pdf"
        )
