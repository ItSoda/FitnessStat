import uuid
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils.timezone import now

from users.models import EmailVerifications, User


@shared_task
def send_email_success_register(name: str, email: str) -> None:
    """Отправка почты после успешной регистрации"""

    # Данные для отправки
    subjects = f"Успешная регистрация в фитнес-клубе FitnessStat"
    message = (
        f"Уважаемый {name}! Поздравляем с успешной регистрацией в сервисе FitnessStat"
    )

    # Отправка
    send_mail(
        subject=subjects,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task
def create_email_verify_task(user_id: int):
    """Создание кода для подтверждения почты"""

    user = User.objects.get(id=user_id)
    expiration = now() + timedelta(hours=24)

    # Создание кода для почты
    record = EmailVerifications.objects.create(
        code=uuid.uuid4(), user=user, expiration=expiration
    )
    record.send_verification_email()
