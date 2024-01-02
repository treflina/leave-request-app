from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError


class ModelTest(TestCase):
    """Test models."""

    def test_create_regular_user_is_successful(self):
        """Test creating a user with a username is successful."""
        username = "test"
        password = "testpassword"
        user = get_user_model().objects.create_user(
            username=username, password=password
        )
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_new_user_without_username_raises_error(self):
        """Test that creating a user without setting a username raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_new_user_with_already_existing_username_should_fail(self):
        get_user_model().objects.create_user(
            username="test1", password="testpassword1"
        )
        with self.assertRaises(IntegrityError):
            get_user_model().objects.create_user(
                username="test1", password="testpassword2"
            )

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            "testuser",
            "testpassword",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
