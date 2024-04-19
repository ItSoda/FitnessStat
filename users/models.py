from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from users.managers import CustomUserManager


# Модель пользователя
class User(AbstractUser):
    """Модель пользователя"""

    phone_number = PhoneNumberField(unique=True)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=50, default="Имя")
    last_name = models.CharField(max_length=50, default="Фамилия")
    patronymic = models.CharField(max_length=50, default="Отчество", blank=True, null=True)
    is_verified_email = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(
        upload_to="avatars",
        null=True,
        blank=True,
        default="avatars/no_profile.png",
    )

    username = None

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "Клиенты | Тренеры"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.patronymic}"
