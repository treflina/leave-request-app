from datetime import date

from django.test import TestCase

from applications.requests.models import Request
from applications.users.models import User
from pdf_creator import create_text_report


class ReportExportTextTest(TestCase):
    def test_create_text_report_returns_text_response(self):
        user = User.objects.create_user(
            username="reportuser",
            password="secretpass",
            first_name="Anna",
            last_name="Kowalska",
            position="pracownik",
        )
        Request.objects.create(
            author=user,
            leave_type="W",
            start_date=date(2025, 1, 5),
            end_date=date(2025, 1, 10),
            days=5,
            status="zaakceptowany",
            signed_by="Kierownik",
        )

        response = create_text_report(
            person=[user.id],
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        self.assertIn("Wykaz wniosków urlopowych", response.content.decode("utf-8"))

    def test_create_certificate_text_report_returns_only_periods(self):
        user = User.objects.create_user(
            username="certificateuser",
            password="secretpass",
            first_name="Jan",
            last_name="Nowak",
            position="pracownik",
        )
        from applications.sickleaves.models import Sickleave

        Sickleave.objects.create(
            employee=user,
            leave_type="C",
            issue_date=date(2025, 1, 5),
            doc_number="ABC123",
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 16),
            additional_info="",
        )
        Sickleave.objects.create(
            employee=user,
            leave_type="C",
            issue_date=date(2025, 2, 1),
            doc_number="XYZ456",
            start_date=date(2025, 2, 18),
            end_date=date(2025, 2, 20),
            additional_info="uwaga",
        )
        Sickleave.objects.create(
            employee=user,
            leave_type="C",
            issue_date=date(2025, 2, 21),
            doc_number="QWE789",
            start_date=date(2025, 2, 21),
            end_date=date(2025, 2, 21),
            additional_info="",
        )
        Sickleave.objects.create(
            employee=user,
            leave_type="C",
            issue_date=date(2025, 2, 25),
            doc_number="ASD112",
            start_date=date(2025, 2, 22),
            end_date=date(2025, 2, 23),
            additional_info="",
        )

        response = create_text_report(
            person=[user.id],
            leave_type="C",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 28),
            attachment=False,
            report_format="certificate",
        )

        text = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pracownik: Nowak Jan", text)
        self.assertIn("10.01.2025-16.01.2025", text)
        self.assertIn("18.02.2025-23.02.2025 (UWAGA: uwaga)", text)
        self.assertNotIn("Wykaz zwolnień lekarskich", text)
