import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from applications.home.models import UploadFile
from applications.users.models import User


class DocumentManagementPermissionTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        settings_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.documents_url = reverse("home_app:documents")
        self.create_user("employee")

    def create_user(
        self, username, role=None, is_staff=False, position="employee"
    ):
        user = User.objects.create_user(
            username=username,
            password="test-password",
            first_name=username,
            last_name="Employee",
            position=position,
        )
        user.role = role
        user.is_staff = is_staff
        user.save(update_fields=["role", "is_staff"])
        return user

    def create_document(self):
        return UploadFile.objects.create(
            file=SimpleUploadedFile("document.txt", b"document"),
            description="Test document",
            category="druki",
        )

    def test_employee_cannot_open_upload_page_or_submit_upload(self):
        employee = User.objects.get(username="employee")
        self.client.force_login(employee)

        response = self.client.get(self.documents_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            self.documents_url,
            {
                "file": SimpleUploadedFile("blocked.txt", b"blocked"),
                "description": "Blocked document",
                "category": "druki",
                "priority": 2,
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            UploadFile.objects.filter(description="Blocked document").exists()
        )

    def test_staff_manager_director_and_it_can_open_upload_page(self):
        permitted_users = (
            self.create_user("staff", is_staff=True),
            self.create_user("manager-role-t", role="T"),
            self.create_user("director", role="S"),
            self.create_user("it", position="Informatyk"),
        )

        for user in permitted_users:
            with self.subTest(username=user.username):
                self.client.force_login(user)
                response = self.client.get(self.documents_url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Dodaj dokument")

    def test_employee_cannot_delete_document(self):
        employee = User.objects.get(username="employee")
        document = self.create_document()
        self.client.force_login(employee)

        response = self.client.post(
            reverse("home_app:delete-file", kwargs={"pk": document.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(UploadFile.objects.filter(pk=document.pk).exists())

    def test_delete_requires_post(self):
        staff_user = self.create_user("staff-get", is_staff=True)
        document = self.create_document()
        self.client.force_login(staff_user)

        response = self.client.get(
            reverse("home_app:delete-file", kwargs={"pk": document.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(UploadFile.objects.filter(pk=document.pk).exists())

    def test_permitted_user_can_delete_document_with_post(self):
        it_user = self.create_user("it-delete", position="Informatyk")
        document = self.create_document()
        self.client.force_login(it_user)

        response = self.client.post(
            reverse("home_app:delete-file", kwargs={"pk": document.pk})
        )

        self.assertRedirects(response, self.documents_url)
        self.assertFalse(
            UploadFile.objects.filter(pk=document.pk).exists()
        )
