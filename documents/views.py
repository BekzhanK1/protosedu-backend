from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from .models import Document
from .serializers import DocumentSerializer
from account.permissions import IsSuperUser
from rest_framework.permissions import AllowAny


class DocumentViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Document instances.
    """

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def list(self, request, *args, **kwargs):
        grade = request.query_params.get("grade")
        doc_type = request.query_params.get("type")
        cache_key = f"documents_list_grade_{grade}_type_{doc_type}"

        print(cache_key)

        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")

        if grade:
            self.queryset = self.queryset.filter(grade=grade)
        if doc_type:
            self.queryset = self.queryset.filter(document_type=doc_type)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response

    def retrieve(self, request, *args, **kwargs):
        document_id = kwargs.get("pk")
        cache_key = f"document_{document_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAuthenticated, IsSuperUser]
        else:
            self.permission_classes = [AllowAny]

        return [permission() for permission in self.permission_classes]
