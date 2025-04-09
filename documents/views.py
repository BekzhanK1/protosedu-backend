from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Document, Subject
from .serializers import DocumentSerializer, SubjectSerializer
from account.permissions import IsSuperUser
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action


class SubjectViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Subject instances.
    """

    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsAuthenticated, IsSuperUser]
        else:
            self.permission_classes = [AllowAny]

        return [permission() for permission in self.permission_classes]

    def list(self, request, *args, **kwargs):
        grade = request.query_params.get("grade")
        if grade is None:
            return Response({"error": "Grade is required."}, status=400)
        cache_key = f"subjects_list_grade_{grade}"

        print(cache_key)

        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")

        if grade:
            self.queryset = self.queryset.filter(grade=grade)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response

    def retrieve(self, request, *args, **kwargs):
        subject_id = kwargs.get("pk")
        cache_key = f"subject_{subject_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)
        return response


class DocumentViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing Document instances.
    """

    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    def list(self, request, *args, **kwargs):
        subject_id = request.query_params.get("subject")
        doc_type = request.query_params.get("type")
        cache_key = f"documents_list_subject_{subject_id}_type_{doc_type}"

        print(cache_key)

        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")

        if not subject_id:
            return Response({"error": "Subject ID is required."}, status=400)

        self.queryset = self.queryset.filter(subject=subject_id)

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

    @action(detail=False, methods=["patch"], url_path="update-document-order")
    def change_order(self, request, *args, **kwargs):
        """
          A custom action to change the order of documents.
        Expects a list of document IDs and their new order values.
        """

        try:
            order_data = request.data
            with transaction.atomic():
                for item in order_data:
                    doc_id = item.get("id")
                    new_order = item.get("order")

                    if not doc_id or not new_order:
                        return Response(
                            {"error": "ID and new order are required"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    document = get_object_or_404(Document, id=int(doc_id))
                    document.order = new_order
                    document.save()

            return Response(
                {"message": "Order updated successfully"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
