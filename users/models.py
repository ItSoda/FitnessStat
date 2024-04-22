from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from users.managers import CustomUserManager


# Модель пользователя
class User(AbstractUser):
    """Модель пользователя"""

    CLIENT = "client"
    COACH = "coach"

    ROLES_CHOICES = (
        (COACH, "coach"),
        (CLIENT, "client"),
    )

    login = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    age = models.PositiveIntegerField(default=0)
    city = models.CharField(max_length=32)
    description = models.TextField()
    phone_number = PhoneNumberField(unique=True)
    email = models.EmailField(blank=True)
    is_verified_email = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(
        upload_to="avatars",
        null=True,
        blank=True,
        default="avatars/no_profile.png",
    )
    experience = models.PositiveIntegerField(default=0)
    role = models.CharField(max_length=6, choices=ROLES_CHOICES, default=CLIENT)

    username = None

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "Клиенты | Тренеры"

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} {self.patronymic}"
