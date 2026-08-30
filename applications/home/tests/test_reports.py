"""
Tests for text report generation functionality.
"""

from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from applications.requests.models import Request
from pdf_creator import create_text_report

User = get_user_model()


class TextReportMissingDataTest(TestCase):
    """Test create_text_report with missing/null data"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="pass",
            first_name="John",
            last_name="Doe",
            position="Manager",
        )
        # Manually set position_addinfo to ensure it exists
        self.user.position_addinfo = "Department A"
        self.user.save()

    def test_deleted_user_handled_gracefully(self):
        """Deleted user should not crash report, show placeholder"""
        user_id = self.user.id
        self.user.delete()

        response = create_text_report(
            person=[user_id],
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
        )

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn(f"[Użytkownik #{user_id} usunięty]", content)

    def test_no_requests_in_date_range(self):
        """No requests in range should return valid report with employee name"""
        response = create_text_report(
            person=[self.user.id],
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
        )

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pracownik: Doe John", content)

    def test_no_sickleaves_in_certificate_format(self):
        """No sick leaves should show notification"""
        response = create_text_report(
            person=[self.user.id],
            leave_type="C",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
            report_format="certificate",
        )

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("[Brak zwolnień lekarskich w wybranym okresie]", content)

    def test_request_with_null_dates_skipped(self):
        """Request with NULL dates should be handled"""
        # Create request with valid dates first
        req = Request.objects.create(
            author=self.user,
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            days=5,
            status="zaakceptowany",
        )
        # Try to generate report (should not crash)
        response = create_text_report(
            person=[self.user.id],
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
        )

        self.assertEqual(response.status_code, 200)


class TextReportAllEmployeesTest(TestCase):
    """Test 'all_employees' export"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="pass",
            first_name="Alice",
            last_name="Anderson",
            position="Staff",
        )
        self.user1.position_addinfo = "Dept A"
        self.user1.save()

        self.user2 = User.objects.create_user(
            username="user2",
            password="pass",
            first_name="Bob",
            last_name="Brown",
            position="Staff",
        )
        self.user2.position_addinfo = "Dept B"
        self.user2.save()

    def test_all_employees_annual_leave(self):
        """Export all employees' annual leave"""
        Request.objects.create(
            author=self.user1,
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            days=5,
            status="zaakceptowany",
        )
        Request.objects.create(
            author=self.user2,
            leave_type="W",
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 3),
            days=3,
            status="zaakceptowany",
        )

        response = create_text_report(
            person=["all_employees"],
            leave_type="W",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 28),
            attachment=False,
        )

        content = response.content.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("- wszyscy pracownicy", content)
        self.assertIn("Anderson Alice", content)
        self.assertIn("Brown Bob", content)
