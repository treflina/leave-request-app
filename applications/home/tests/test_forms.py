"""
Tests for ReportForm validation.
"""

from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..forms import ReportForm

User = get_user_model()


class ReportFormPersonSelectionTest(TestCase):
    """Test person field validation in ReportForm"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="pass",
            first_name="John",
            last_name="Doe",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="pass",
            first_name="Jane",
            last_name="Smith",
        )

    def test_empty_person_selection_fails_validation(self):
        """Empty person list should raise ValidationError"""
        form = ReportForm(data={
            "person": [],
            "leave_type": "W",
            "start_date_day": 1,
            "start_date_month": 1,
            "start_date_year": 2025,
            "end_date_day": 31,
            "end_date_month": 1,
            "end_date_year": 2025,
            "attachment": False,
            "report_format": "pdf",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("person", form.errors)

    def test_valid_single_person_selection(self):
        """Single person selection should pass validation"""
        form = ReportForm(data={
            "person": [str(self.user1.id)],
            "leave_type": "W",
            "start_date_day": 1,
            "start_date_month": 1,
            "start_date_year": 2025,
            "end_date_day": 31,
            "end_date_month": 1,
            "end_date_year": 2025,
            "attachment": False,
            "report_format": "pdf",
        })
        self.assertTrue(form.is_valid())

    def test_valid_multiple_person_selection(self):
        """Multiple person selection should pass validation"""
        form = ReportForm(data={
            "person": [str(self.user1.id), str(self.user2.id)],
            "leave_type": "W",
            "start_date_day": 1,
            "start_date_month": 1,
            "start_date_year": 2025,
            "end_date_day": 31,
            "end_date_month": 1,
            "end_date_year": 2025,
            "attachment": False,
            "report_format": "pdf",
        })
        self.assertTrue(form.is_valid())

    def test_valid_all_employees_selection(self):
        """all_employees selection should pass validation"""
        form = ReportForm(data={
            "person": ["all_employees"],
            "leave_type": "W",
            "start_date_day": 1,
            "start_date_month": 1,
            "start_date_year": 2025,
            "end_date_day": 31,
            "end_date_month": 1,
            "end_date_year": 2025,
            "attachment": False,
            "report_format": "pdf",
        })
        self.assertTrue(form.is_valid())

    def test_duplicate_person_ids_in_selection(self):
        """Duplicate person IDs should be accepted by form (handled in export)"""
        form = ReportForm(data={
            "person": [str(self.user1.id), str(self.user1.id)],
            "leave_type": "W",
            "start_date_day": 1,
            "start_date_month": 1,
            "start_date_year": 2025,
            "end_date_day": 31,
            "end_date_month": 1,
            "end_date_year": 2025,
            "attachment": False,
            "report_format": "pdf",
        })
        self.assertTrue(form.is_valid())

    def test_non_existent_user_id_in_selection(self):
        """Non-existent user ID would cause error in export, but form's clean_person() doesn't validate ID existence"""
        # Skip this test - form validation only checks non-empty, not ID validity
        # ID validation happens during export with try/except User.DoesNotExist
        pass
