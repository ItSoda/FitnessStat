from django.urls import path
from rest_framework import routers

from . import views

app_name = "users"


urlpatterns = [
    path("phone/send-code/", views.PhoneNumberSendSMSView.as_view(), name="phone-send"),
    path(
        "phone/verify-code/",
        views.PhoneNumberVerificationView.as_view(),
        name="phone-code-verify",
    ),
    path(
        "email/verify/<str:email>/<uuid:code>/",
        views.EmailVerificationUserUpdateView.as_view(),
        name="email_verify",
    ),
    path(
        "email/check-email-verify/",
        views.CheckEmailVerifyAPIView.as_view(),
        name="check-email-verify",
    ),
    path(
        "statistics/get-statistics/<str:login>/",
        views.UserStatisticsInfoAPIView.as_view(),
        name="get-all-statistics",
    ),
]
