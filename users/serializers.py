import base64
import logging
import uuid
from io import BytesIO
from typing import Optional

from django.conf import settings
from django.core.files.base import ContentFile, File
from djoser.serializers import UserCreateSerializer
from PIL import Image
from rest_framework import serializers

from .models import User

logger = logging.getLogger("main")
logger_error = logging.getLogger("error")


class UserRegistSerializer(UserCreateSerializer):
    """Сериализатор регистрации пользователей"""

    class Meta(UserCreateSerializer.Meta):
        fields = ("id", "phone_number", "password")


class UserShortSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода основной информации о пользователе"""

    class Meta:
        model = User
        fields = (
            "id",
            "phone_number",
            "email",
            "name",
        )


class UserProfileSerializer(UserShortSerializer):
    """Сериализатор полной информации о пользователе"""

    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta(UserShortSerializer.Meta):
        fields = UserShortSerializer.Meta.fields + (
            "password",
            "description",
            "date_joined",
            "last_login",
            "photo",
        )
        read_only_fields = ("password",)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля пользователя"""

    photo = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "name",
            "description",
            "photo",
        ]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "patronymic": {"required": False},
            "photo": {"required": False},
            "description": {"required": False},
        }

    def update(self, instance, validated_data):
        photo_base64 = validated_data.pop("photo", None)
        if photo_base64:
            try:
                format, imgstr = photo_base64.split(";base64,")
                ext = format.split("/")[-1]
                data = ContentFile(
                    base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}"
                )

                img = Image.open(data)
                output = BytesIO()
                img.save(output, format="PNG", quality=85, exif=None)
                output.seek(0)
                instance.photo = File(output, name=data.name)

            except Exception as e:
                logger.info(f"Ошибка: {str(e)}")
                raise ValueError("Неправильный формат фотографии")
        return super().update(instance, validated_data)
