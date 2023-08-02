from django.db import models
from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager, models.Manager):
    def _create_user(
        self, username, password, is_staff, is_active, is_superuser, **extra_fields
    ):
        if not username:
            raise ValueError("User must have a username.")
        user = self.model(
            username=username,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=is_active,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, True, False, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        return self._create_user(username, password, True, True, True, **extra_fields)
