from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
import logging

from posts.models import Post
from posts.pagination.posts import PostPagination
from posts.serializers.posts import PostSerializer


logger_error = logging.getLogger("error")


class PostAllAPIView(APIView):
    """Получение постов на основной странице"""

    def paginate_queryset(self, queryset):
        page = self.request.query_params.get("page")
        if page:
            paginator = PostPagination()
            return paginator.paginate_queryset(queryset, self.request)

        return queryset

    def get(self, request, *args, **kwargs):
        try:
            posts = Post.objects.order_by("-created_at")

            # Пагинация постов
            posts_with_pagination = self.paginate_queryset(posts)

            # Получение постов в json формате
            posts_serializer_data = PostSerializer(
                posts_with_pagination, many=True, context={"request": request}
            ).data

            return Response(
                {
                    "posts": {
                        "count": posts.count(),
                        "results": posts_serializer_data,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger_error.error(f"Ошибка получения списка постов: {str(e)}")
            return Response(
                {"error": "Ошибка получения списка постов"},
                status=status.HTTP_400_BAD_REQUEST,
            )
