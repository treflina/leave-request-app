from django.conf import settings
from django.db import models


class Message(models.Model):
    msg_title = models.CharField("Tytuł wiadomości", max_length=100)
    msg_content = models.TextField("Treść wiadomości")
    employees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Pracownicy",
    )

    class Meta:
        verbose_name = "Wiadomość"
        verbose_name_plural = "Wiadomości"

    def __str__(self):
        return self.msg_title
