from django.urls import path

from .views import posts

app_name = "posts"


urlpatterns = [
    path("all/", posts.PostAllAPIView.as_view(), name="posts-all"),
]
