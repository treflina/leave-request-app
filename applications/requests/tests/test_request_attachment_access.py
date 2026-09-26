import tempfile
import uuid

from django.core.files.base import ContentFile
from django.test import TransactionTestCase, override_settings
from django.urls import reverse

from applications.requests.models import Request as LeaveRequest
from applications.users.models import User


class RequestAttachmentAccessTests(TransactionTestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        suffix = uuid.uuid4().hex[:8]
        self.owner = self.create_user(f"owner-{suffix}")
        self.recipient = self.create_user(f"rcpt-{suffix}")
        self.other_user = self.create_user(f"other-{suffix}")
        self.staff_user = self.create_user(f"staff-{suffix}")
        self.staff_user.is_staff = True
        self.staff_user.save(update_fields=["is_staff"])

        self.leave_request = LeaveRequest.objects.create(
            author=self.owner,
            send_to_person=self.recipient,
            leave_type="W",
            status="oczekujący",
            days=1,
        )
        self.leave_request.attachment.save(
            "sensitive.pdf",
            ContentFile(b"private attachment content"),
            save=True,
        )
        self.download_url = reverse(
            "requests_app:download_request_attachment",
            kwargs={"pk": self.leave_request.pk},
        )

    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            password="test-password",
            first_name=username,
            last_name="Employee",
            position="employee",
        )

    def assert_user_can_download(self, user):
        self.client.force_login(user)
        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(
            b"".join(response.streaming_content),
            b"private attachment content",
        )
        response.close()

    def test_owner_can_download(self):
        self.assert_user_can_download(self.owner)

    def test_assigned_recipient_can_download(self):
        self.assert_user_can_download(self.recipient)

    def test_staff_can_download(self):
        self.assert_user_can_download(self.staff_user)

    def test_unrelated_employee_cannot_download(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users_app:user-login"), response["Location"])

    def test_direct_media_url_is_not_served(self):
        response = self.client.get(
            f"/media/{self.leave_request.attachment.name}"
        )

        self.assertEqual(response.status_code, 404)
