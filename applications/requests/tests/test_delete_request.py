from django.test import TestCase
from django.urls import reverse

from applications.requests.models import Request as LeaveRequest
from applications.users.models import User


class DeleteRequestViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="test-password",
            first_name="Owner",
            last_name="User",
            position="employee",
            current_leave=5,
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="test-password",
            first_name="Other",
            last_name="User",
            position="employee",
            current_leave=2,
        )
        self.leave_request = LeaveRequest.objects.create(
            author=self.owner,
            leave_type="W",
            days=3,
            status="oczekujący",
        )
        self.url = reverse(
            "requests_app:delete_request",
            kwargs={"pk": self.leave_request.pk},
        )

    def test_other_user_cannot_delete_or_receive_leave_credit(self):
        self.client.force_login(self.other_user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            LeaveRequest.objects.filter(pk=self.leave_request.pk).exists()
        )
        self.owner.refresh_from_db()
        self.other_user.refresh_from_db()
        self.assertEqual(self.owner.current_leave, 5)
        self.assertEqual(self.other_user.current_leave, 2)

    def test_owner_can_withdraw_pending_request_and_get_leave_credit(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"], reverse("requests_app:user_requests")
        )
        self.assertFalse(
            LeaveRequest.objects.filter(pk=self.leave_request.pk).exists()
        )
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.current_leave, 8)

    def test_get_does_not_withdraw_request(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            LeaveRequest.objects.filter(pk=self.leave_request.pk).exists()
        )

    def test_owner_cannot_withdraw_non_pending_request(self):
        self.leave_request.status = "zaakceptowany"
        self.leave_request.save(update_fields=["status"])
        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            LeaveRequest.objects.filter(pk=self.leave_request.pk).exists()
        )
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.current_leave, 5)
