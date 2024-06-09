from django.db import models

class Message(models.Model):
    """Модель для сообщений"""

    chat = models.ForeignKey("Chat", on_delete=models.CASCADE)
    sender = models.ForeignKey("users.User", on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
    image = models.ImageField(
        upload_to="chats",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    viewed = models.BooleanField(default=False)
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    json_data = models.JSONField(blank=True, null=True, default=dict)
    position = models.PositiveBigIntegerField(default=0)
    is_edited = models.BooleanField(default=False)

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ("created_at",)

    def __str__(self):
        return f"message: {self.sender} | date: {self.created_at}"

