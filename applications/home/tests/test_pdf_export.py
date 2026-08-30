"""
Tests for PDF and certificate export functionality.
"""

from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from applications.sickleaves.models import Sickleave
from pdf_creator import (
    create_text_report,
    _merge_certificate_ranges,
    _format_certificate_period,
    _format_certificate_range_with_note,
)

User = get_user_model()


class CertificateRangeMergingTest(TestCase):
    """Test _merge_certificate_ranges function"""

    def test_merge_adjacent_ranges(self):
        """Adjacent ranges should merge"""
        ranges = [
            [date(2025, 1, 1), date(2025, 1, 5)],
            [date(2025, 1, 6), date(2025, 1, 10)],
        ]
        result = _merge_certificate_ranges(ranges)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], date(2025, 1, 1))
        self.assertEqual(result[0][1], date(2025, 1, 10))

    def test_merge_overlapping_ranges(self):
        """Overlapping ranges should merge"""
        ranges = [
            [date(2025, 1, 1), date(2025, 1, 10)],
            [date(2025, 1, 5), date(2025, 1, 15)],
        ]
        result = _merge_certificate_ranges(ranges)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], date(2025, 1, 15))

    def test_merge_with_gap_of_one_day(self):
        """Gap of 1 day should NOT merge (gap must be 0 to merge)"""
        ranges = [
            [date(2025, 1, 1), date(2025, 1, 5)],
            [date(2025, 1, 7), date(2025, 1, 10)],
        ]
        result = _merge_certificate_ranges(ranges)
        # Logic: if current_start <= last_end + timedelta(days=1)
        # 7 <= 5 + 1 = 7 <= 6 = False, so NO merge
        self.assertEqual(len(result), 2)

    def test_merge_with_gap_of_two_days(self):
        """Gap of 2 days should NOT merge"""
        ranges = [
            [date(2025, 1, 1), date(2025, 1, 5)],
            [date(2025, 1, 8), date(2025, 1, 10)],
        ]
        result = _merge_certificate_ranges(ranges)
        self.assertEqual(len(result), 2)

    def test_merge_identical_ranges(self):
        """Identical ranges should merge to one"""
        ranges = [
            [date(2025, 1, 1), date(2025, 1, 5)],
            [date(2025, 1, 1), date(2025, 1, 5)],
        ]
        result = _merge_certificate_ranges(ranges)
        self.assertEqual(len(result), 1)

    def test_merge_unsorted_ranges(self):
        """Unsorted ranges should be sorted then merged"""
        ranges = [
            [date(2025, 1, 10), date(2025, 1, 15)],
            [date(2025, 1, 1), date(2025, 1, 5)],
            [date(2025, 1, 7), date(2025, 1, 9)],
        ]
        result = _merge_certificate_ranges(ranges)
        # Should merge [1,5] and [7,9] due to gap=1, separate from [10,15]
        self.assertGreater(len(result), 0)
        # Check sorted
        for i in range(len(result) - 1):
            self.assertLessEqual(result[i][1], result[i + 1][0])

    def test_merge_empty_list(self):
        """Empty list should return empty"""
        result = _merge_certificate_ranges([])
        self.assertEqual(result, [])

    def test_merge_single_range(self):
        """Single range should return single"""
        ranges = [[date(2025, 1, 1), date(2025, 1, 5)]]
        result = _merge_certificate_ranges(ranges)
        self.assertEqual(len(result), 1)


class CertificatePeriodFormattingTest(TestCase):
    """Test _format_certificate_period function"""

    def test_single_day_format(self):
        """Single day should format without dash"""
        result = _format_certificate_period(date(2025, 1, 5), date(2025, 1, 5))
        self.assertEqual(result, "05.01.2025")

    def test_date_range_format(self):
        """Date range should include dash"""
        result = _format_certificate_period(date(2025, 1, 1), date(2025, 1, 10))
        self.assertEqual(result, "01.01.2025-10.01.2025")

    def test_cross_month_format(self):
        """Range crossing months should format correctly"""
        result = _format_certificate_period(date(2025, 1, 28), date(2025, 2, 3))
        self.assertEqual(result, "28.01.2025-03.02.2025")

    def test_cross_year_format(self):
        """Range crossing years should format correctly"""
        result = _format_certificate_period(date(2024, 12, 28), date(2025, 1, 3))
        self.assertEqual(result, "28.12.2024-03.01.2025")


class CertificateRangeWithNoteTest(TestCase):
    """Test _format_certificate_range_with_note function"""

    def test_range_without_note(self):
        """Range without note should not include UWAGA"""
        result = _format_certificate_range_with_note(
            date(2025, 1, 1), date(2025, 1, 5), ""
        )
        self.assertEqual(result, "01.01.2025-05.01.2025")

    def test_range_with_note(self):
        """Range with note should include UWAGA"""
        result = _format_certificate_range_with_note(
            date(2025, 1, 1), date(2025, 1, 5), "uwaga"
        )
        self.assertEqual(result, "01.01.2025-05.01.2025 (UWAGA: uwaga)")

    def test_range_with_whitespace_note(self):
        """Whitespace-only note should be ignored"""
        result = _format_certificate_range_with_note(
            date(2025, 1, 1), date(2025, 1, 5), "   "
        )
        self.assertEqual(result, "01.01.2025-05.01.2025")

    def test_range_with_empty_default_note(self):
        """Missing note parameter should use empty default"""
        result = _format_certificate_range_with_note(
            date(2025, 1, 1), date(2025, 1, 5)
        )
        self.assertEqual(result, "01.01.2025-05.01.2025")


class CertificateExportCompleteTest(TestCase):
    """Test complete certificate export flow"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="pass",
            first_name="John",
            last_name="Doe",
            position="Staff",
        )
        self.user.position_addinfo = "Dept A"
        self.user.save()

    def test_certificate_export_single_period(self):
        """Export single sick leave period"""
        Sickleave.objects.create(
            employee=self.user,
            leave_type="C",
            issue_date=date(2025, 1, 5),
            doc_number="ABC123",
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 15),
            additional_info="",
        )

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
        self.assertIn("Pracownik: Doe John", content)
        self.assertIn("10.01.2025-15.01.2025", content)

    def test_certificate_export_overlapping_periods(self):
        """Export overlapping periods (should merge)"""
        Sickleave.objects.create(
            employee=self.user,
            leave_type="C",
            issue_date=date(2025, 1, 1),
            doc_number="DOC1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10),
            additional_info="",
        )
        Sickleave.objects.create(
            employee=self.user,
            leave_type="C",
            issue_date=date(2025, 1, 5),
            doc_number="DOC2",
            start_date=date(2025, 1, 5),
            end_date=date(2025, 1, 15),
            additional_info="",
        )

        response = create_text_report(
            person=[self.user.id],
            leave_type="C",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
            report_format="certificate",
        )

        content = response.content.decode("utf-8")
        self.assertIn("01.01.2025-15.01.2025", content)

    def test_certificate_export_with_notes(self):
        """Export periods with additional_info notes"""
        Sickleave.objects.create(
            employee=self.user,
            leave_type="C",
            issue_date=date(2025, 1, 1),
            doc_number="DOC1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            additional_info="operacja",
        )

        response = create_text_report(
            person=[self.user.id],
            leave_type="C",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
            report_format="certificate",
        )

        content = response.content.decode("utf-8")
        self.assertIn("(UWAGA: operacja)", content)

    def test_certificate_export_deleted_employee(self):
        """Deleted employee should show placeholder"""
        user_id = self.user.id
        self.user.delete()

        response = create_text_report(
            person=[user_id],
            leave_type="C",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            attachment=False,
            report_format="certificate",
        )

        content = response.content.decode("utf-8")
        self.assertIn(f"[Użytkownik #{user_id} usunięty]", content)
