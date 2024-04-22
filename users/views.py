import logging
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_ratelimit.decorators import ratelimit

from .serializers import (
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserShortSerializer,
)

logger_error = logging.getLogger("error")
logger = logging.getLogger("main")


class CustomTokenRefreshView(TokenRefreshView):
    """Запрос для refresh access токена с отключением логирования"""

    @method_decorator(ratelimit(key="ip", rate="5/s"))
    def post(self, request, *args, **kwargs):
        logger.disabled = True
        response = super().post(request, *args, **kwargs)
        logger.disabled = False
        return response


class UserProfileRetrieveAPI(RetrieveAPIView):
    """Запрос полной информации о пользователе"""

    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    @method_decorator(ratelimit(key="ip", rate="5/s"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class LogoutAPIView(APIView):
    """Запрос на выход из аккаунта"""

    @method_decorator(ratelimit(key="ip", rate="5/s"))
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Успешный выход из аккаунта "},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            logger_error.error(f"Ошибка выхода из аккаунта: {str(e)}")
            return Response(
                {"error": "Произошла ошибка удаления. Токен уже удален!"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserProfileUpdateAPIView(APIView):
    """Запрос на изменение профиля пользователя"""

    @method_decorator(ratelimit(key="ip", rate="5/s"))
    def patch(self, request, *args, **kwargs):
        user = self.request.user
        try:
            serializer = UserProfileUpdateSerializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                data = UserProfileSerializer(user).data
                return Response(data, status=status.HTTP_200_OK)
            else:
                raise ValueError("Данные не валидные")
        except Exception as e:
            logger_error.error(f"Ошибка обновления аккаунта пользователя: {str(e)}")
            return Response(
                {"error": "Неправильный формат данных"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SignInTGNotifyAPIView(TokenObtainPairView):
    """Авторизация"""

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            return response
        except Exception as e:
            logger_error.error(f"Ошибка авторизации: {str(e)}")
            return Response(
                {
                    "error": "Неправильные учетные данные. Пожалуйста, проверьте ваш логин и пароль и попробуйте снова."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
