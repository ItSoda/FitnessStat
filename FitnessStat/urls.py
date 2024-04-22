from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenVerifyView

from .admin import custom_admin_site
from djoser.views import UserViewSet
from .yasg import urlpatterns as doc_url
from users.views import (
    CustomTokenRefreshView,
    LogoutAPIView,
    SignInTGNotifyAPIView,
    UserProfileRetrieveAPI,
)


urlpatterns = [
    path("admin_panel/", custom_admin_site.urls),
    path("auth/users/", UserViewSet.as_view({"post": "create"}), name="user_create"),
    path("auth/users/me/", UserProfileRetrieveAPI.as_view(), name="user_view"),
    path("api/token/", SignInTGNotifyAPIView.as_view(), name="authorization"),
    path("api/logout/", LogoutAPIView.as_view(), name="logout"),
    path("api/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]

urlpatterns += doc_url
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += (path("__debug__/", include("debug_toolbar.urls")),)
