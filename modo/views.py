from rest_framework import viewsets, filters, status
from .models import Test, Question, Content, AnswerOption, TestAnswer
from .serializers import (
    TestSerializer,
    QuestionSerializer,
    ContentSerializer,
    AnswerOptionSerializer,
)
from account.permissions import IsSuperUserOrStaffOrReadOnly, IsAuthenticated
from rest_framework.exceptions import ValidationError

from rest_framework.response import Response
from django.db import transaction

MAX_ANSWER_OPTIONS = 4
MAX_CONTENTS = 4


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["order", "title"]
    ordering = ["order"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        request = self.request
        child_id = request.query_params.get("child_id")
        user = request.user

        test_answers = None
        if self.action == "retrieve" and user.is_authenticated:
            test = self.get_object()
            if user.is_parent:
                test_answers = TestAnswer.objects.filter(
                    test=test, child_id=child_id
                ).select_related("answer_option", "question")
            elif user.is_student:
                test_answers = TestAnswer.objects.filter(
                    test=test, user=user
                ).select_related("answer_option", "question")

        context.update(
            {
                "request": request,
                "child_id": child_id,
                "test_answers": test_answers,
                "action": self.action,
            }
        )
        return context

    def create(self, request):
        test = request.data
        print(test)
        test_data = {
            "title": test["title"],
            "description": test["description"],
            "test_type": test["test_type"],
        }
        test_serializer = self.get_serializer(data=test_data)
        if test_serializer.is_valid():
            test_instance = test_serializer.save()
            for question in test["questions"]:
                question["test"] = test_instance.pk
                question_serializer = QuestionSerializer(data=question)
                if question_serializer.is_valid():
                    contents = {"text": question["title"]}
                    if question["image"]:
                        contents["image"] = question["image"]
                    print(contents, question["answers"])
                    question_serializer.save_with_contents_and_answers(
                        contents, question["answers"]
                    )
                if not question_serializer.is_valid():
                    print(question_serializer.errors)
        return Response(test_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        test_data = self.get_serializer(instance).data

        questions_data = []
        for question in instance.questions.all():
            question_data = QuestionSerializer(question).data
            questions_data.append(question_data)

        # print(test_data)
        test_data["questions"] = questions_data
        return Response(test_data, status=status.HTTP_200_OK)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["order", "title"]
    ordering = ["order"]

    def get_queryset(self):
        test_id = self.request.query_params.get("test_id")
        if not test_id:
            raise ValidationError({"detail": "Parameter 'test_id' is required."})
        queryset = super().get_queryset().filter(test_id=test_id)
        return queryset


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order"]
    ordering = ["order"]

    def create(self, request, *args, **kwargs):
        question_id = request.data["question"]
        existing_count = self.queryset.filter(question_id=question_id).count()
        if existing_count >= MAX_CONTENTS:
            raise ValidationError(
                {"detail": "Total content count for this question must not exceed 4."}
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnswerOptionViewSet(viewsets.ModelViewSet):
    queryset = AnswerOption.objects.all()
    serializer_class = AnswerOptionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def create(self, request, *args, **kwargs):
        question_id = (
            request.data[0]["question"]
            if isinstance(request.data, list)
            else request.data["question"]
        )
        existing_count = self.queryset.filter(question_id=question_id).count()
        new_count = len(request.data) if isinstance(request.data, list) else 1

        if existing_count + new_count > MAX_ANSWER_OPTIONS:
            raise ValidationError(
                {
                    "detail": "Total answer options count for this question must not exceed 4."
                }
            )

        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            with transaction.atomic():
                self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()


class TestAnswerViewSet(viewsets.ModelViewSet):
    queryset = TestAnswer.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_parent:
            child_id = self.request.query_params.get("child_id")
            if not child_id:
                raise ValidationError({"detail": "Parameter 'child_id' is required."})
            queryset = super().get_queryset().filter(child_id=child_id)
        elif user.is_student:
            queryset = super().get_queryset().filter(user_id=user.id)
        return queryset
