import json
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from pprint import pprint

from account.models import Child, User
from .models import (
    TestAnswer,
    Test,
    Question,
    Content,
    AnswerOption,
    TestResult,
    TestCategory,
    TEST_TYPE,
)
from .serializers import (
    FullTestCreateSerializer,
    FullTestUpdateSerializer,
    TestCategorySerializer,
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
from .utils import clean_parsed_data, parse_nested_form_data

from rest_framework.response import Response
from django.db import transaction

MAX_ANSWER_OPTIONS = 8
MAX_CONTENTS = 8
VALID_TEST_TYPES = [choice[0] for choice in TEST_TYPE]


class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["order", "title"]
    ordering = ["order"]

    @action(
        detail=False,
        methods=["post"],
        url_path="create-full",
        url_name="create_full",
        permission_classes=[IsSuperUserOrStaffOrReadOnly],
    )
    def create_full(self, request, *args, **kwargs):
        parsed_data = parse_nested_form_data(request.data, request.FILES)
        cleaned_data = clean_parsed_data(parsed_data)

        serializer = FullTestCreateSerializer(data=cleaned_data)
        serializer.is_valid(raise_exception=True)
        test = serializer.save()
        return Response(
            TestSerializer(test, context={"request": request}).data, status=201
        )

    @action(detail=True, methods=["put"], url_path="update-full")
    def update_full(self, request, *args, **kwargs):
        test = self.get_object()
        parsed_data = parse_nested_form_data(request.data, request.FILES)
        cleaned_data = clean_parsed_data(parsed_data)

        serializer = FullTestUpdateSerializer(test, data=cleaned_data, partial=True)
        serializer.is_valid(raise_exception=True)
        test = serializer.save()
        return Response(TestSerializer(test, context={"request": request}).data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        category_id = request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        test_type = request.query_params.get("test_type")
        if test_type:
            if test_type not in VALID_TEST_TYPES:
                return Response(
                    {"error": f"test_type `{test_type}` is not in {VALID_TEST_TYPES}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(test_type=test_type)

        child_id = request.query_params.get("child_id")
        serializer = self.get_serializer(
            queryset, context={"request": self.request, "child_id": child_id}, many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        child_id = request.query_params.get("child_id")
        serializer = self.get_serializer(
            instance, context={"request": self.request, "child_id": child_id}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


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

        # Step 1: Identify the acting entity (user or child)
        if user.is_student:
            entity: User = user
            result_filter = {"user": entity}
        elif user.is_parent:
            child_id = request.query_params.get("child_id")
            if not child_id:
                return Response(
                    {"detail": "Child ID is required for parent users."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            entity: Child = get_object_or_404(Child, pk=child_id, parent__user=user)
            result_filter = {"child": entity}
        else:
            return Response(
                {"detail": "You do not have permission to answer questions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Step 2: Get question and answer option
        question_id = request.query_params.get("question_id")
        if not question_id:
            return Response(
                {"detail": "Question ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question = get_object_or_404(Question, pk=question_id)
        answer_option_id = request.data.get("answer_option")

        if not answer_option_id:
            return Response(
                {"detail": "Answer option is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer_option = get_object_or_404(
            AnswerOption, pk=answer_option_id, question=question
        )

        # Step 3: Find or create the test result for current attempt
        result_filter["test"] = question.test
        last_result = (
            TestResult.objects.filter(**result_filter)
            .order_by("-attempt_number")
            .first()
        )

        if last_result and not last_result.is_finished:
            test_result = last_result
        else:
            next_attempt = (last_result.attempt_number + 1) if last_result else 1
            test_result = TestResult.objects.create(
                **result_filter, attempt_number=next_attempt
            )

        # Step 4: Save or update the answer for this question in current attempt
        TestAnswer.objects.update_or_create(
            test_result=test_result,
            question=question,
            user=entity if user.is_student else None,
            child=entity if user.is_parent else None,
            defaults={
                "answer_option": answer_option,
                "is_correct": answer_option.is_correct,
            },
        )

        # Step 5: Calculate progress and update the test result
        answers = TestAnswer.objects.filter(test_result=test_result)
        answered_questions = answers.count()
        correct_answers = answers.filter(is_correct=True).count()
        total_questions = question.test.questions.count()

        test_result.total_questions = total_questions
        test_result.correct_answers = correct_answers
        test_result.score = (
            round((correct_answers / total_questions) * 100) if total_questions else 0
        )
        test_result.is_finished = answered_questions == total_questions
        test_result.save()

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
        attempt_number = request.query_params.get("attempt_number")
        if attempt_number:
            try:
                attempt_number = int(attempt_number)
            except ValueError:
                return Response(
                    {"detail": "Attempt number must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            attempt_number = None

        if not test_id:
            return Response(
                {"detail": "Test ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        test = get_object_or_404(Test, pk=test_id)

        result_queryset = TestResult.objects.filter(
            test=test, **({"user": entity} if user.is_student else {"child": entity})
        )

        if attempt_number is not None:
            result_queryset = result_queryset.filter(attempt_number=attempt_number)

        test_result = result_queryset.order_by("-attempt_number").first()

        if not test_result:
            return Response(
                {"detail": "No test results found for this test."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TestResultSerializer(test_result, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TestCategoryViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing TestCategory objects.
    """

    queryset = TestCategory.objects.all()
    serializer_class = TestCategorySerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]
