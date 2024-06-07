import logging
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from users.models import User
from users.services import (
    get_statistics_by_filter,
    get_user_by_login,
    proccess_email_verification,
    proccess_phone_verification,
    send_phone_verify_task,
)

from .serializers import (
    BodyVolumeSerializer,
    ExternalIndicatorSerializer,
    PhysicalIndicatorSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
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


class SignInAPIView(APIView):
    """Запрос на авторизацию"""

    def post(self, request):
        phone_number = request.data.get("phone_number")

        if not phone_number:
            return Response(
                {"error": "Номер телефона обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(phone_number=phone_number).first()

        if not user:
            return Response(
                {"error": "Пользователь не найден."}, status=status.HTTP_400_BAD_REQUEST
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )


# PHONE NUMBER VIEWS
class PhoneNumberVerificationView(APIView):
    """Верификация СМС-кода"""

    def post(self, request, *args, **kwargs):
        try:
            # Получаем данные
            phone_number = request.data.get("phone_number")
            code = request.data.get("code")

            phone_verify_result = proccess_phone_verification(code, phone_number)

            if phone_verify_result:
                return Response(
                    {"message": "СМС-код успешно подтвержден"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"message": "СМС-код неправильный или просрочен"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger_error.error(f"Ошибка верификации СМС-кода: {str(e)}")
            return Response(
                {"error": "Произошла ошибка"}, status=status.HTTP_400_BAD_REQUEST
            )


class PhoneNumberSendSMSView(APIView):
    """Отправка СМС-кода"""

    def post(self, request, *args, **kwargs):
        try:
            # Получаем данные
            phone_number = request.data.get("phone_number")

            send_phone_verify_task(phone_number)
            return Response(
                {"message": "СМС-код успешно отправлен"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger_error.error(f"Ошибка отправки смс-кода: {str(e)}")
            return Response(
                {"error": "Произошла ошибка."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# EMAIL VIEWS
class EmailVerificationUserUpdateView(APIView):
    """Верификация почты и обновления у пользователя подтверждения почты"""

    def get(self, request, *args, **kwargs):
        # Получение данных
        code = kwargs.get("code")
        email = kwargs.get("email")

        email_verify, user = proccess_email_verification(code=code, email=email)

        try:
            if email_verify:
                return Response(
                    {"is_verified_email": user.is_verified_email},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"error": "Код был просрочен или неправильный"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger_error.error(f"Ошибка верицикации почты {str(e)}")
            return Response(
                {"error": "Произошла ошибка"}, status=status.HTTP_400_BAD_REQUEST
            )


class CheckEmailVerifyAPIView(APIView):
    """Проверка верификации почты пользователя"""

    def get(self, request, *args, **kwargs):
        user = self.request.user

        try:
            # Если почта не подтверждена
            if not user.is_verified_email:
                return Response(
                    {"message": "Почта не подтверждена."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {"is_verified_email": user.is_verified_email}, status=status.HTTP_200_OK
            )

        except Exception as e:
            logger_error.error(f"Ошибка верификации почты пользователя {str(e)}")
            return Response(
                {"error": "Произошла ошибка."}, status=status.HTTP_400_BAD_REQUEST
            )


class UserStatisticsInfoAPIView(APIView):
    """Запрос для получения статистики пользователя"""

    def get(self, request, *args, **kwargs):
        try:
            user_login = self.kwargs.get("login") # Получение имени пользователя
            statistics_filter = self.request.GET.get("statistics")
            user = get_user_by_login(user_login) # Получение пользователя

            statistics = get_statistics_by_filter(user=user, statistics_filter=statistics_filter) # Получение статистики с помощью фильтра
            # Сериалиазация списка статистики
            if statistics_filter == "external_indicator":
                statistic_serializer = ExternalIndicatorSerializer(statistics, many=True, context={"request": request}).data
            elif statistics_filter == "physical_indicator":
                statistic_serializer = PhysicalIndicatorSerializer(statistics, many=True, context={"request": request}).data
            elif statistics_filter == "body_volume":
                statistic_serializer = BodyVolumeSerializer(statistics, many=True, context={"request": request}).data
            else:
                return Response([], status=status.HTTP_200_OK)


            return Response(
                statistic_serializer, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger_error.error(f"Ошибка вывода статистики пользователя: {str(e)}")
            return Response(
                {"error": "Не получилось вывести статистику пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )


