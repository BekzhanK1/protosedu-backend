from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.core.cache import cache

from account.models import Child
from account.permissions import IsParent, IsSuperUser
from account.serializers import ChildSerializer
import json


class ChildrenViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [IsParent | IsSuperUser]

    def retrieve(self, request, pk=None):
        cache_key = f"child_data_{pk}"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            queryset = self.get_queryset()
            child = get_object_or_404(queryset, pk=pk)
            serializer = self.serializer_class(child)
            cache.set(cache_key, serializer.data, timeout=300)
            return Response(serializer.data)

        else:
            return Response(cached_data)

    def create(self, request):
        parent = request.user.parent
        if parent.children.count() >= 3:
            return Response(
                {"message": "You can't add more than 3 children"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = request.data.copy()
        data["parent"] = parent.pk
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        if self.request.user.is_parent:
            parent = self.request.user.parent
            return Child.objects.filter(parent=parent)
        if self.request.user.is_superuser:
            return Child.objects.all()

        return Child.objects.none()
