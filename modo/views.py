from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema

from account.models import Child, User
from .models import TestAnswer, Test, Question, Content, AnswerOption, TestResult
from .serializers import (
    TestResultSerializer,
    TestSerializer,
    TestQuestionSerializer,
    ContentSerializer,
    AnswerOptionSerializer,
)
from account.permissions import IsParent, IsStudent, IsSuperUserOrStaffOrReadOnly
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        child_id = request.query_params.get("child_id")
        serializer = self.get_serializer(
            queryset, context={"request": self.request, "child_id": child_id}, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": self.request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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
                question_serializer = TestQuestionSerializer(data=question)
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


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = TestQuestionSerializer
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
        data = request.data

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "question" in data:
            items = [data]
        else:
            raise ValidationError({"detail": "Invalid data format"})

        question_id = items[0]["question"]
        existing_count = self.queryset.filter(question_id=question_id).count()
        if existing_count + len(items) > MAX_ANSWER_OPTIONS:
            raise ValidationError(
                {
                    "detail": "Total answer options count for this question must not exceed 4."
                }
            )

        for item in items:
            if item["option_type"] == "image" and not item.get("image"):
                raise ValidationError(
                    {"detail": "Image must be provided for option_type 'image'."}
                )
            if item["option_type"] == "text" and not item.get("text"):
                raise ValidationError(
                    {"detail": "Text must be provided for option_type 'text'."}
                )

        serializer = self.get_serializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()


class AnswerQuestionAPIView(APIView):
    permission_classes = [IsParent | IsStudent]

    def post(self, request, *args, **kwargs):
        user: User = request.user

        if user.is_student:
            entity = user
        elif user.is_parent:
            child_id = request.query_params.get("child_id")
            if not child_id:
                return Response(
                    {"detail": "Child ID is required for parent users."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            entity: Child = get_object_or_404(Child, pk=child_id, parent__user=user)
        else:
            return Response(
                {"detail": "You do not have permission to answer questions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        question_id = request.query_params.get("question_id")
        if not question_id:
            return Response(
                {"detail": "Question ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question = get_object_or_404(Question, pk=question_id)

        answer_options = question.answer_options.all()
        if not answer_options.exists():
            return Response(
                {"detail": "No answer options available for this question."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data
        answer_option = data.get("answer_option")
        if not answer_option:
            return Response(
                {"detail": "Answer option is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer_option_instance = get_object_or_404(
            AnswerOption, pk=answer_option, question=question
        )

        with transaction.atomic():
            filter_kwargs = {"question": question}
            result_kwargs = {"test": question.test}
            if user.is_student:
                filter_kwargs["user"] = entity
                result_kwargs["user"] = entity
            else:
                filter_kwargs["child"] = entity
                result_kwargs["child"] = entity

            test_answer, _ = TestAnswer.objects.update_or_create(
                question=question,
                defaults={
                    "answer_option": answer_option_instance,
                    "is_correct": answer_option_instance.is_correct,
                    **filter_kwargs,
                },
            )

            answers = TestAnswer.objects.filter(
                question__test=question.test,
                **({"user": entity} if user.is_student else {"child": entity}),
            )

            answered_questions = answers.count()
            correct_answers = answers.filter(is_correct=True).count()

            total_questions = question.test.questions.count()

            TestResult.objects.update_or_create(
                defaults={
                    "score": (correct_answers // total_questions) * 100,
                    "correct_answers": correct_answers,
                    "total_questions": total_questions,
                    "is_finished": (
                        True if total_questions == answered_questions else False
                    ),
                },
                **result_kwargs,
            )

        return Response(
            {"detail": "Answer submitted successfully."},
            status=status.HTTP_201_CREATED,
        )


class TestReviewAPIView(APIView):
    permission_classes = [IsParent | IsStudent]

    @extend_schema(
        summary="Review Test Results",
        description="Allows students or parents to review test results for a specific test.",
        responses={
            200: TestResultSerializer,
            400: {"description": "Bad Request"},
            403: {"description": "Forbidden"},
            404: {"description": "Not Found"},
        },
        tags=["Tests"],
        parameters=[
            {
                "name": "test_id",
                "required": True,
                "in": "query",
                "description": "ID of the test to review.",
                "type": "integer",
            },
            {
                "name": "child_id",
                "required": False,
                "in": "query",
                "description": "ID of the child (required for parent users).",
                "type": "integer",
            },
        ],
    )
    def get(self, request, *args, **kwargs):
        user: User = request.user

        if user.is_student:
            entity = user
        elif user.is_parent:
            child_id = request.query_params.get("child_id")
            if not child_id:
                return Response(
                    {"detail": "Child ID is required for parent users."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            entity: Child = get_object_or_404(Child, pk=child_id, parent__user=user)
        else:
            return Response(
                {"detail": "You do not have permission to review tests."},
                status=status.HTTP_403_FORBIDDEN,
            )

        test_id = request.query_params.get("test_id")
        if not test_id:
            return Response(
                {"detail": "Test ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test = get_object_or_404(Test, pk=test_id)

        result_queryset = TestResult.objects.filter(
            test=test, **({"user": entity} if user.is_student else {"child": entity})
        )

        if not result_queryset.exists():
            return Response(
                {"detail": "No results found for this test."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TestResultSerializer(
            result_queryset.first(), context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
