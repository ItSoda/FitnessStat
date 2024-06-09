from django.db import models


class Chat(models.Model):
    """Модель для чата"""

    users = models.ManyToManyField("users.User")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "чат"
        verbose_name_plural = "Чаты"

    def __str__(self) -> str:
        return f"Чат: {self.id}"
    