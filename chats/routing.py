from django.urls import path

from .consumers import 

websocket_urlpatterns = [
    path("ws/chat/default-chat/", consumers.ChatConsumer.as_asgi()),
]