from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """Класс для кастомной пагинации"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
    max_page_number = 10000

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param, 1)

        if int(page_number) > self.max_page_number:
            raise NotFound(detail="Page not found", code=404)

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        next_page_number = self.page.number + 1 if self.page.has_next() else None
        previous_page_number = (
            self.page.number - 1 if self.page.has_previous() else None
        )
        return Response(
            {
                "count": self.page.paginator.count,
                "next": next_page_number,
                "previous": previous_page_number,
                "results": data,
            }
        )


class PostPagination(CustomPagination):
    """Класс для кастомной пагинации услуг"""

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
    max_page_number = 10000
