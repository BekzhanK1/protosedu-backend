from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Child, Student
from account.permissions import HasSubscription, IsSuperUserOrStaffOrReadOnly

from .models import (
    Answer,
    CanvasImage,
    Chapter,
    Content,
    Course,
    Lesson,
    Question,
    Section,
    Task,
    TaskCompletion,
)
from .serializers import (
    CanvasImageSerializer,
    ChapterSerializer,
    ContentSerializer,
    CourseSerializer,
    LessonSerializer,
    QuestionSerializer,
    SectionSerializer,
    TaskSerializer,
    TaskSummarySerializer,
)

GAME_COST_CONST = 20
CACHE_TIMEOUT = 1


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = f"course_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        serializer = self.serializer_class(instance, context={"request": request})
        cache.set(cache_key, serializer.data, CACHE_TIMEOUT)

        return Response(serializer.data)

    def list(self, request):
        user = request.user
        child_id = request.query_params.get("child_id", None)

        if user.is_student:
            student = get_object_or_404(Student, user=user)
            cache_key = f"courses_{student.grade}_{student.language}"
            queryset = Course.objects.filter(
                grade=student.grade,
                language=student.language,
            )
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            cache_key = f"courses_{child.grade}_{child.language}"
            queryset = Course.objects.filter(
                grade=child.grade,
                language=child.language,
            )
        else:
            cache_key = "courses_all"
            queryset = Course.objects.all()

        print("cache_key", cache_key)

        cached_data = cache.get(cache_key)
        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")

        queryset = (
            Course.objects.filter(grade=student.grade, language=student.language)
            if user.is_student
            else (
                Course.objects.filter(grade=child.grade, language=child.language)
                if user.is_parent and child_id
                else Course.objects.all()
            )
        )

        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        cache.set(cache_key, serializer.data, CACHE_TIMEOUT)

        return Response(serializer.data)

    def create(self, request):
        user = request.user
        data = request.data.copy()
        data["created_by"] = user.id
        serializer = self.serializer_class(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Section.objects.filter(course_id=self.kwargs["course_pk"]).order_by(
            "order"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = f"section_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        serializer = self.serializer_class(instance, context={"request": request})
        cache.set(cache_key, serializer.data, CACHE_TIMEOUT)

        return Response(serializer.data)

    def list(self, request, course_pk=None):
        cache_key = f"sections_{course_pk}"
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        queryset = self.get_queryset()
        serializer = SectionSerializer(
            queryset, many=True, context={"request": request}
        )
        cache.set(cache_key, serializer.data, CACHE_TIMEOUT)

        return Response(serializer.data)

    def create(self, request, course_pk=None):
        data = request.data.copy()

        if isinstance(data, list):
            for item in data:
                item["course"] = course_pk
        else:
            data["course"] = course_pk

        serializer = self.serializer_class(data=data, many=isinstance(data, list))
        if serializer.is_valid():
            sections = serializer.save()
            return Response(
                self.serializer_class(sections, many=isinstance(data, list)).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    serializer_class = ChapterSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = f"chapter_{instance.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        serializer = self.serializer_class(instance, context={"request": request})
        cache.set(cache_key, serializer.data, CACHE_TIMEOUT)

        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        section_pk = self.kwargs["section_pk"]
        cache_key = f"chapters_{section_pk}"
        cached_data = cache.get(cache_key)

        if cached_data:
            print("Cache hit", cached_data)
            return Response(cached_data)

        print("Cache miss")
        queryset = self.get_queryset()
        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        cache.set(cache_key, serializer.data, CACHE_TIMEOUT)

        return Response(serializer.data)

    def get_queryset(self):
        return Chapter.objects.filter(section_id=self.kwargs["section_pk"]).order_by(
            "order"
        )

    def create(self, request, section_pk=None, course_pk=None, *args, **kwargs):
        data = request.data.copy()
        data["section"] = section_pk
        serializer = self.serializer_class(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ContentViewSet(viewsets.ModelViewSet):
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Content.objects.filter(chapter_id=self.kwargs["chapter_pk"]).order_by(
            "order"
        )

    def create(self, request, chapter_pk=None):
        data = request.data.copy()
        data["chapter"] = chapter_pk
        serializer = self.serializer_class(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[IsSuperUserOrStaffOrReadOnly],
    )
    def update_contents(
        self, request, course_pk=None, section_pk=None, chapter_pk=None
    ):
        contents_data = request.data.get("contents")
        if not contents_data:
            return Response(
                {"detail": "Contents data is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                for content_data in contents_data:
                    content = get_object_or_404(Content, id=content_data["id"])
                    content.order = content_data.get("order", content.order)
                    content.title = content_data.get("title", content.title)
                    content.description = content_data.get(
                        "description", content.description
                    )
                    content.save()
            return Response(
                {"detail": "Contents updated successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": "Error during updating contents."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [HasSubscription, IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Lesson.objects.filter(chapter_id=self.kwargs["chapter_pk"]).order_by(
            "order"
        )

    def create(self, request, course_pk=None, section_pk=None, chapter_pk=None):
        data = request.data.copy()
        if isinstance(data, list):
            for item in data:
                item["chapter"] = chapter_pk
                item["content_type"] = "lesson"
        else:
            data["chapter"] = chapter_pk
            data["content_type"] = "lesson"

        serializer = self.serializer_class(
            data=data, many=isinstance(data, list), context={"request": request}
        )
        if serializer.is_valid():
            lessons = serializer.save()
            return Response(
                self.serializer_class(lessons, many=isinstance(data, list)).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [HasSubscription, IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Task.objects.filter(chapter_id=self.kwargs["chapter_pk"]).order_by(
            "order"
        )

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return TaskSummarySerializer
        return TaskSerializer

    def create(self, request, chapter_pk=None, section_pk=None, course_pk=None):
        data = request.data.copy()
        if isinstance(data, list):
            for item in data:
                item["chapter"] = chapter_pk
                item["content_type"] = "task"
        else:
            data["chapter"] = chapter_pk
            data["content_type"] = "task"

        serializer = self.get_serializer(
            data=data, many=isinstance(data, list), context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [HasSubscription, IsSuperUserOrStaffOrReadOnly]

    def get_queryset(self):
        return Question.objects.filter(task_id=self.kwargs["task_pk"])

    def create(self, request, *args, **kwargs):
        print(request.data)
        data = request.data.copy()

        if isinstance(data, list):
            for item in data:
                item["task"] = self.kwargs["task_pk"]
        else:
            data["task"] = self.kwargs["task_pk"]

        try:
            with transaction.atomic():
                serializer = self.serializer_class(
                    data=data, many=isinstance(data, list), context={"request": request}
                )
                if serializer.is_valid():
                    questions = serializer.save()
                    TaskCompletion.objects.filter(
                        task_id=self.kwargs["task_pk"]
                    ).all().delete()
                    return Response(
                        self.serializer_class(
                            questions, many=isinstance(data, list)
                        ).data,
                        status=status.HTTP_201_CREATED,
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"message": "Error during question creation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def partial_update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        data = request.data.copy()
        data["task"] = self.kwargs["task_pk"]

        try:
            with transaction.atomic():
                serializer = self.serializer_class(
                    instance, data=data, partial=partial, context={"request": request}
                )
                if serializer.is_valid():
                    question = serializer.save()
                    return Response(
                        self.serializer_class(question).data, status=status.HTTP_200_OK
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"message": "Error during question update", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="answer",
        permission_classes=[IsAuthenticated],
    )
    def answer(self, request, *args, **kwargs):
        question = self.get_object()
        user = request.user
        child_id = request.data.get("child_id")
        # answer_text = request.data.get("answer")
        is_correct = request.data.get("is_correct")

        # if not answer_text:
        #     return Response(
        #         {"message": "Answer is required"}, status=status.HTTP_400_BAD_REQUEST
        #     )

        # is_correct = self.validate_answer(question, answer_text)

        if user.is_student:
            result = self.handle_answer(
                user=user,
                question=question,
                # answer_text=answer_text,
                is_correct=is_correct,
            )
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            result = self.handle_answer(
                child=child,
                question=question,
                # answer_text=answer_text,
                is_correct=is_correct,
            )
        else:
            return Response(
                {"message": "Invalid request. Parent must provide child_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)

    # def validate_answer(self, question, answer):
    #     if question.question_type in [
    #         "multiple_choice_text",
    #         "multiple_choice_images",
    #         "true_false",
    #         "drag_position",
    #         "number_line",
    #     ]:
    #         return int(answer) == question.correct_answer
    #     elif question.question_type in ["drag_and_drop_text", "drag_and_drop_images"]:
    #         return answer == question.correct_answer
    #     elif question.question_type == "mark_all":
    #         return set(answer) == set(question.correct_answer)
    #     return False

    def handle_answer(self, user=None, child=None, question=None, is_correct=False):
        entity = user.student if user else child

        try:
            with transaction.atomic():
                is_answer_exists = Answer.objects.filter(
                    user=user, child=child, question=question
                ).exists()

                if is_answer_exists:
                    return {
                        "message": "Answer processed, but no reward is given",
                        "is_correct": is_correct,
                    }

                Answer.objects.create(
                    user=user if user else None,
                    child=child if child else None,
                    question=question,
                    # answer=answer_text,
                    is_correct=is_correct,
                )

                if is_correct:
                    entity.add_question_reward()
                    entity.update_level()

                task = question.task
                total_questions = task.questions.count()
                answered_questions = Answer.objects.filter(
                    user=user, child=child, question__task=task
                ).count()

                correct_answers = Answer.objects.filter(
                    user=user, child=child, question__task=task, is_correct=True
                ).count()

                wrong_answers = answered_questions - correct_answers

                if answered_questions == total_questions:
                    task_completion, created = TaskCompletion.objects.get_or_create(
                        user=user if user else None,
                        child=child if child else None,
                        task=task,
                    )
                    task_completion.correct = correct_answers
                    task_completion.wrong = wrong_answers
                    task_completion.save()

                    entity.update_streak()

                return {
                    "message": "Answer processed, reward is given",
                    "is_correct": is_correct,
                }

        except Exception as e:
            return {
                "message": f"Error processing answer: {str(e)}",
                "is_correct": False,
            }


class PlayGameView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        child_id = request.query_params.get("child_id", None)
        game_cost = GAME_COST_CONST

        if user.is_student:
            return self.deduct_stars(user.student, game_cost)
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return self.deduct_stars(child, game_cost)

        return Response(
            {"message": "Invalid request. Parent must provide child_id."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def deduct_stars(self, entity, cost):
        if entity.stars < cost:
            return Response(
                {"message": "Not enough stars", "is_enough": False},
                status=status.HTTP_200_OK,
            )
        entity.stars -= cost
        entity.save()
        return Response(
            {"message": f"{cost} stars have been deducted", "is_enough": True},
            status=status.HTTP_200_OK,
        )


class DeleteCanvasImage(APIView):
    permission_classes = [IsSuperUserOrStaffOrReadOnly]

    def delete(self, request):
        image_ids = request.data.get("image_ids")

        if not image_ids:
            return Response(
                {"message": "Image id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(image_ids, list):
            return Response(
                {"message": "Image id must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                for image_id in image_ids:
                    if not image_id:
                        return Response(
                            {"message": "Image id is required"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    canvas_image = get_object_or_404(CanvasImage, image_id=image_id)
                    canvas_image.delete()
        except Exception as e:
            return Response(
                {"message": f"Error deleting canvas image: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"message": "Canvas images has been deleted"}, status=status.HTTP_200_OK
        )
