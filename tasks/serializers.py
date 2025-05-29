from django.shortcuts import get_object_or_404
from rest_framework import serializers

from account.models import Child

from .models import (
    Answer,
    CanvasImage,
    Chapter,
    Complaint,
    Content,
    ContentNode,
    Course,
    Image,
    Lesson,
    Question,
    Section,
    Task,
    TaskCompletion,
)


class AnswerSerializer(serializers.Serializer):
    answer = serializers.CharField()


class LessonSerializer(serializers.ModelSerializer):
    used_in_content_node = serializers.SerializerMethodField()

    def get_used_in_content_node(self, obj):
        return hasattr(obj, "content_node") and obj.content_node is not None

    class Meta:
        model = Lesson
        fields = "__all__"


class LessonSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "video_url", "text", "order"]


class ImageSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["id", "value"]

    def get_id(self, obj):
        return obj.option_id

    def get_value(self, obj):
        return obj.image.url


class CanvasImageSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = CanvasImage
        fields = "image_id", "value"

    def get_value(self, obj):
        return obj.image.url


class QuestionSerializer(serializers.ModelSerializer):
    is_attempted = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, read_only=True)
    canvas_images = CanvasImageSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = "__all__"

    def get_is_attempted(self, obj):
        request = self.context.get("request", None)
        if not request:
            return False

        user = request.user
        child_id = request.query_params.get("child_id")
        if user.is_student:
            return Answer.objects.filter(user=user, question=obj).exists()
        elif user.is_parent:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return Answer.objects.filter(child=child, question=obj).exists()
        return False

    def get_is_correct(self, obj):
        request = self.context.get("request", None)
        if not request:
            return False

        user = request.user
        child_id = request.query_params.get("child_id")
        if user.is_student:
            return Answer.objects.filter(
                user=user, question=obj, is_correct=True
            ).exists()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return Answer.objects.filter(
                child=child, question=obj, is_correct=True
            ).exists()
        return False

    def create(self, validated_data):
        question = Question.objects.create(**validated_data)

        if question.question_type in ["multiple_choice_images", "drag_and_drop_images"]:
            self._handle_images(question)

        self._handle_canvas_images(question)

        return question

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if instance.question_type in ["multiple_choice_images", "drag_and_drop_images"]:
            self._handle_images(instance)
        else:
            instance.images.all().delete()

        self._handle_canvas_images(instance)

        instance.save()
        return instance

    def _handle_canvas_images(self, question):
        canvas_images_data = self.context.get("request").FILES

        if not canvas_images_data:
            return

        options = []

        for key in canvas_images_data:
            if "canvasImage_" in key:
                image_id = key.split("_")[
                    1
                ]  # Expecting the key to be formatted as 'canvasImage_imageId'
                image_file = canvas_images_data[key]

                image = question.canvas_images.filter(image_id=image_id).first()
                if image:
                    image.image = image_file
                    image.save()
                else:
                    image = CanvasImage.objects.create(
                        question=question, image=image_file, image_id=image_id
                    )

        question.save()

    def _handle_images(self, question):
        images_data = self.context.get("request").FILES

        if not images_data:
            return

        options = []

        for key in images_data:
            if "image_" in key:
                option_id = key.split("_")[
                    1
                ]  # Expecting the key to be formatted as 'image_OPTIONID'
                image_file = images_data[key]

                image = question.images.filter(option_id=option_id).first()
                if image:
                    image.image = image_file
                    image.save()
                else:
                    image = Image.objects.create(
                        question=question, image=image_file, option_id=option_id
                    )

                options.append({"id": option_id, "value": image.image.url})

        question.options = options
        question.save()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.question_type in ["multiple_choice_images", "drag_and_drop_images"]:
            representation["options"] = representation.pop("images", [])
        return representation


class TaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    is_completed = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    correct_questions = serializers.SerializerMethodField()
    incorrect_questions = serializers.SerializerMethodField()
    answered_questions = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    used_in_content_node = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = "__all__"

    def get_used_in_content_node(self, obj):
        return hasattr(obj, "content_node") and obj.content_node is not None

    def get_task_completion(self, obj):
        request = self.context.get("request", None)
        if not request:
            return None

        user = request.user
        child_id = request.query_params.get("child_id")

        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task=obj).first()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task=obj).first()
        return None

    def get_answered_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        if task_completion:
            return task_completion.correct + task_completion.wrong
        return 0

    def get_progress(self, obj):
        answered_questions = self.get_answered_questions(obj)
        total_questions = self.get_total_questions(obj)
        if total_questions == 0:
            return 0
        return (answered_questions / total_questions) * 100

    def get_incorrect_questions(self, obj):
        return self.get_total_questions(obj) - self.get_correct_questions(obj)

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_correct_questions(self, obj):
        task_completion = self.get_task_completion(obj)
        return task_completion.correct if task_completion else 0

    def get_is_completed(self, obj):
        return bool(self.get_task_completion(obj))


class TaskSummarySerializer(TaskSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "chapter",
            "questions",
            "order",
            "progress",
            "answered_questions",
            "is_completed",
            "total_questions",
            "correct_questions",
            "incorrect_questions",
            "used_in_content_node",
        ]


class ContentSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = "__all__"

    def get_is_completed(self, obj):
        request = self.context.get("request", None)
        if not request:
            return None

        if obj.content_type == "task":
            user = request.user
            child_id = request.query_params.get("child_id")

            if user.is_student:
                return TaskCompletion.objects.filter(user=user, task=obj).exists()
            elif user.is_parent and child_id:
                child = get_object_or_404(Child, parent=user.parent, pk=child_id)
                return TaskCompletion.objects.filter(child=child, task=obj).exists()
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.content_type != "task":
            representation.pop("is_completed", None)
        return representation


class ContentNodeSerializer(serializers.ModelSerializer):
    lesson = serializers.SerializerMethodField()
    task = serializers.SerializerMethodField()

    class Meta:
        model = ContentNode
        fields = ["id", "title", "description", "chapter", "order", "lesson", "task"]

    def get_lesson(self, obj):
        if obj.lesson:
            return {"id": obj.lesson.id, "title": obj.lesson.title}
        return None

    def get_task(self, obj):
        if obj.task:
            return {"id": obj.task.id, "title": obj.task.title}
        return None


class ChapterSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = "__all__"

    def get_total_tasks(self, obj):
        return Task.objects.filter(chapter=obj).count()

    def get_completed_tasks(self, obj):
        request = self.context.get("request", None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get("child_id")
        if user.is_student:
            return TaskCompletion.objects.filter(user=user, task__chapter=obj).count()
        elif user.is_parent and child_id:

            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(child=child, task__chapter=obj).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0


class SectionSerializer(serializers.ModelSerializer):
    chapters = ChapterSerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = "__all__"

    def get_total_tasks(self, obj):
        return Task.objects.filter(chapter__section=obj).count()

    def get_completed_tasks(self, obj):
        request = self.context.get("request", None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get("child_id")
        if user.is_student:
            return TaskCompletion.objects.filter(
                user=user, task__chapter__section=obj
            ).count()
        elif user.is_parent and child_id:

            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(
                child=child, task__chapter__section=obj
            ).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0


class SectionSummarySerializer(serializers.ModelSerializer):
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = [
            "id",
            "title",
            "description",
            "order",
            "total_tasks",
            "completed_tasks",
            "percentage_completed",
        ]

    def get_total_tasks(self, obj):
        return Task.objects.filter(chapter__section=obj).count()

    def get_completed_tasks(self, obj):
        request = self.context.get("request", None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get("child_id")
        if user.is_student:
            return TaskCompletion.objects.filter(
                user=user, task__chapter__section=obj
            ).count()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(
                child=child, task__chapter__section=obj
            ).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0


class CourseSerializer(serializers.ModelSerializer):
    sections = SectionSummarySerializer(many=True, read_only=True)
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    percentage_completed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_total_tasks(self, obj):
        # Adjusted query to correctly traverse the relationship
        return Task.objects.filter(chapter__section__course=obj).count()

    def get_completed_tasks(self, obj):
        request = self.context.get("request", None)
        if not request:
            return 0

        user = request.user
        child_id = request.query_params.get("child_id")
        if user.is_student:
            return TaskCompletion.objects.filter(
                user=user, task__chapter__section__course=obj
            ).count()
        elif user.is_parent and child_id:
            child = get_object_or_404(Child, parent=user.parent, pk=child_id)
            return TaskCompletion.objects.filter(
                child=child, task__chapter__section__course=obj
            ).count()
        return 0

    def get_percentage_completed(self, obj):
        total_tasks = self.get_total_tasks(obj)
        completed_tasks = self.get_completed_tasks(obj)
        return (completed_tasks * 100 / total_tasks) if total_tasks > 0 else 0


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        task = instance.question.task
        rep["user_email"] = instance.user.email if instance.user else None
        rep["question_id"] = instance.question.id
        rep["question_text"] = instance.question.question_text
        rep["question"] = instance.question.title
        rep["task"] = task.title
        rep["task_id"] = task.id
        rep["chapter"] = task.chapter.title
        rep["chapter_id"] = task.chapter.id
        rep["section"] = task.chapter.section.title
        rep["section_id"] = task.chapter.section.id
        rep["course"] = task.chapter.section.course.name
        rep["course_id"] = task.chapter.section.course.id
        rep["grade"] = task.chapter.section.course.grade
        rep["language"] = task.chapter.section.course.language
        return rep
