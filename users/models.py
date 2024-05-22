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
        return f"{self.name}"


class BodyVolume(models.Model):
    """Модель для обьема тела"""

    user_statistics = models.ForeignKey("UserStatistic", on_delete=models.CASCADE)
    bust = models.PositiveIntegerField(default=0)
    biceps = models.PositiveIntegerField(default=0)
    hip = models.PositiveIntegerField(default=0)
    calf = models.PositiveIntegerField(default=0)
    waist = models.PositiveIntegerField(default=0)
    forearm = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "обьем тела"
        verbose_name_plural = "Обьем тела"

    def __str__(self) -> str:
        return f"Обьем тела для статистики: {self.user_statistics.user.username}"


class PhysicalIndicator(models.Model):
    """Модель для физических показателей"""

    user_statistics = models.ForeignKey("UserStatistic", on_delete=models.CASCADE)
    weight = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "физические показатели"
        verbose_name_plural = "Физические показатели"

    def __str__(self) -> str:
        return f"Физические показатели для статистики: {self.user_statistics.user.username}"


class ExternalIndicator(models.Model):
    """Модель для внешних показателей"""

    user_statistics = models.ForeignKey("UserStatistic", on_delete=models.CASCADE)
    number_of_steps_per_day = models.PositiveBigIntegerField(default=0)
    amount_of_KCAL_per_day = models.PositiveIntegerField(default=0)
    proteins = models.PositiveIntegerField(default=0)
    fats = models.PositiveIntegerField(default=0)
    carbohydrates = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "внешний показатель"
        verbose_name_plural = "Внешние показатели"

    def __str__(self) -> str:
        return (
            f"Внешние показатели для статистики: {self.user_statistics.user.username}"
        )


class UserStatistic(models.Model):
    """Модель для статистики пользователя"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body_volumes = models.ManyToManyField(BodyVolume)
    physical_indicators = models.ManyToManyField(PhysicalIndicator)
    external_indicators = models.ManyToManyField(ExternalIndicator)

    class Meta:
        verbose_name = "статистику пользователя"
        verbose_name_plural = "Статистика пользователя"

    def __str__(self) -> str:
        return f"Статистика пользователя: {self.user.username}"


class PhoneNumberVerifySMS(models.Model):
    """Модель для смс-кодов"""

    code = models.CharField(unique=True, max_length=4)
    phone_number = PhoneNumberField()
    created = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField()

    class Meta:
        verbose_name = "код подтверждения"
        verbose_name_plural = "Коды подтверждения"

    def __str__(self) -> str:
        return f"СМС-код для {self.phone_number}"

    def send_verification_phone(self):
        from users.services import send_verification_phone

        send_verification_phone(self.phone_number, self.code)

    def is_expired(self):
        from users.services import is_expired

        is_expired(self)


class EmailVerifications(models.Model):
    """Модель для верификации почты"""

    code = models.UUIDField(unique=True, null=True, blank=True)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    expiration = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Код для подтверждения почты {self.user.email}"

    def send_verification_email(self):
        from users.services import send_verification_email

        send_verification_email(self.user.email, self.code)

    def is_expired(self):
        from users.services import is_expired

        is_expired(self)
