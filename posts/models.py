from django.db import models

from users.models import User


class ImagePost(models.Model):
    """Модель для фотографий постов"""

    image = models.ImageField(upload_to="posts")


class Post(models.Model):
    """Модель для постов"""

    title = models.CharField(max_length=128)
    description = models.CharField(max_length=1200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    images = models.ManyToManyField(ImagePost, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "пост"
        verbose_name_plural = "Посты"

    def __str__(self) -> str:
        return f"Пост {self.id}"
