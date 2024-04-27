from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from twilio.rest import Client
from django.utils import timezone
import logging
import random
from datetime import timedelta
from django.core.mail import EmailMessage, send_mail

logger_error = logging.getLogger("error")


# PHONE VERIFICATION
def send_verification_phone(phone_number, code):
    account_sid = settings.ACCOUNT_SID_TWILIO
    auth_token = settings.AUTH_TOKEN_TWILIO

    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            from_="+19146104867", to=f"{phone_number}", body=f"code - {code}"
        )
    except Exception as e:
        logger_error.info(f"error: {str(e)}")


def is_expired(self):
    if timezone.now() >= self.expiration:
        self.delete()
        self.save()
        return True
    return False


def proccess_phone_verification(code, phone_number):
    from users.models import PhoneNumberVerifySMS

    phone_numbers = PhoneNumberVerifySMS.objects.filter(
        code=code, phone_number=phone_number
    )
    try:
        if phone_numbers.exists() and not phone_numbers.last().is_expired():
            phone_numbers.last().delete()
            return True
        return False
    except Exception as e:
        return False


def send_phone_verify_task(phone_number):
    from users.models import PhoneNumberVerifySMS

    expiration = timezone.now() + timedelta(hours=24)
    code = str(random.randint(1000, 9999))
    record = PhoneNumberVerifySMS.objects.create(
        code=code, phone_number=phone_number, expiration=expiration
    )
    record.send_verification_phone()


# EMAIL VERIFICATION
def send_verification_email(user_email: str, code: int) -> None:
    """Отправка почты пользователю"""

    link = reverse("users:email_verify", kwargs={"email": user_email, "code": code})
    full_link = f"{settings.DOMAIN_NAME}{link}"
    subjects = f"Подтверждение учетной записи для {user_email}"
    message = "Для подтверждения электронной почты {} перейдите по ссылке: {}.".format(
        user_email,
        full_link,
    )

    send_mail(
        subject=subjects,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False,
    )


def proccess_email_verification(code: int, email: str) -> list:
    """Верификация email и обновления подтверждения почты у пользователя"""

    from users.models import EmailVerifications, User

    user = get_object_or_404(User, email=email)
    email_verifications = EmailVerifications.objects.filter(code=code, user=user)
    try:
        if email_verifications.exists() and not email_verifications.last().is_expired():
            user.is_verified_email = True
            user.save()
            return True, user
        return False, user
    except Exception as e:
        logger_error.error(f"Ошибка подтверждения почты у пользователя: {str(e)}")
        return False, user
