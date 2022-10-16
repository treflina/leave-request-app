from datetime import datetime, date

from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.db.models import Q

from django.apps import apps


class UserManager(BaseUserManager, models.Manager):
    def _create_user(
        self, username, password, is_staff, is_active, is_superuser, **extra_fields
    ):
        user = self.model(
            username=username,
            is_staff=is_staff,
            is_superuser=is_superuser,
            is_active=is_active,
            **extra_fields
        )
        user.set_password(password)
        # using indicates what base we're working with
        user.save(using=self.db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, True, False, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        return self._create_user(username, password, True, True, True, **extra_fields)
