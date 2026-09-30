from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from applications.requests.models import Request
from applications.users.models import User


class UpcomingLeavesTest(TestCase):
    def test_manager_sees_own_and_direct_reports_upcoming_leaves(self):
        manager = User.objects.create_user(
            username="manager",
            password="secretpass",
            first_name="Marek",
            last_name="Kierownik",
            position="kierownik",
            role="K",
        )
        employee = User.objects.create_user(
            username="employee",
            password="secretpass",
            first_name="Anna",
            last_name="Pracownik",
            position="pracownik",
            manager=manager,
        )
        unrelated_employee = User.objects.create_user(
            username="unrelated",
            password="secretpass",
            first_name="Jan",
            last_name="Inny",
            position="pracownik",
        )
        today = date.today()
        own_leave = Request.objects.create(
            author=manager,
            leave_type="W",
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=1),
            days=1,
        )
        employee_leave = Request.objects.create(
            author=employee,
            leave_type="W",
            start_date=today + timedelta(days=2),
            end_date=today + timedelta(days=2),
            days=1,
        )
        Request.objects.create(
            author=unrelated_employee,
            leave_type="W",
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=3),
            days=1,
        )

        self.client.force_login(manager)
        response = self.client.get(reverse("home_app:index"))

        self.assertEqual(
            list(response.context["upcoming_leaves"]),
            [own_leave, employee_leave],
        )
        self.assertContains(response, "Marek Kierownik (Ty)")
        self.assertContains(response, "Anna Pracownik")
        self.assertContains(response, "border-emerald-600")