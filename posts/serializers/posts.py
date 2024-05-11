from rest_framework import serializers
from ..models import Post, ImagePost
from users.serializers import UserShortSerializer


class ImagePostSerializer(serializers.ModelSerializer):
    """Сериализатор для изображений поста"""

    class Meta:
        model = ImagePost
        fields = ("id", "image")


class PostSerializer(serializers.ModelSerializer):
    """Сериализатор для постов"""

    creator = UserShortSerializer()
    images = ImagePostSerializer(many=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")

    class Meta:
        model = Post
        fields = ("id", "title", "description", "creator", "images", "created_at")
