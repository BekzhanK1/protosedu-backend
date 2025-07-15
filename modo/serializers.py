from rest_framework import serializers
from django.db import transaction
from .models import (
    Test,
    Question,
    Content,
    AnswerOption,
    TestAnswer,
    TestCategory,
    TestResult,
)
from drf_spectacular.utils import extend_schema_field


class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = "__all__"


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = "__all__"

    def validate(self, data):
        if data["content_type"] == "text":
            if not data.get("text"):
                raise serializers.ValidationError(
                    "Text must be filled when content_type is 'text'."
                )
            if data.get("image"):
                raise serializers.ValidationError(
                    "Image must be empty when content_type is 'text'."
                )
        else:
            if not data.get("image"):
                raise serializers.ValidationError(
                    "Image must be filled when content_type is not 'text'."
                )
            if data.get("text"):
                raise serializers.ValidationError(
                    "Text must be empty when content_type is not 'text'."
                )
        return data


class TestQuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    contents = ContentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = "__all__"

    def save_with_contents_and_answers(self, contents, answers):
        instance = self.save()

        for key in contents:
            if key == "text":
                Content.objects.create(
                    question=instance,
                    content_type=key,
                    text=contents[key],
                )
            else:
                Content.objects.create(
                    question=instance, content_type=key, image=contents[key]
                )

        for answer in answers:
            AnswerOption.objects.create(
                question=instance, text=answer["text"], is_correct=answer["is_correct"]
            )


class SingleTestQuestionSerializer(serializers.ModelSerializer):
    answer_options = AnswerOptionSerializer(many=True, read_only=True)
    contents = ContentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = "__all__"

    def create(self, validated_data):
        """Create a new question with its contents and answer options"""
        contents_data = self.context["request"].data.get("contents", [])
        answer_options_data = self.context["request"].data.get("answer_options", [])

        return self._save_question_with_relations(
            validated_data, contents_data, answer_options_data
        )

    def update(self, instance, validated_data):
        """Update existing question and replace its contents and answer options"""
        contents_data = self.context["request"].data.get("contents", [])
        answer_options_data = self.context["request"].data.get("answer_options", [])
        print(self.context["request"].data)
        print(contents_data, answer_options_data)
        # Update the question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        return self._save_question_with_relations(
            validated_data, contents_data, answer_options_data, instance
        )

    def _save_question_with_relations(
        self, validated_data, contents_data, answer_options_data, instance=None
    ):
        """Helper method to save question with its related objects"""
        print(answer_options_data)
        with transaction.atomic():
            if instance is None:
                instance = Question.objects.create(**validated_data)
            else:
                instance.save()
                instance.contents.all().delete()
                instance.answer_options.all().delete()

            if not isinstance(contents_data, list):
                raise serializers.ValidationError("Contents must be a list.")

            for i, content_data in enumerate(contents_data):
                content_type = content_data.get("content_type", "text")

                if content_type not in ["text", "image"]:
                    raise serializers.ValidationError(
                        f"Unsupported content type: {content_type}"
                    )

                content_kwargs = {
                    "question": instance,
                    "content_type": content_type,
                    "order": content_data.get("order", i),
                }

                if content_type == "text":
                    text_value = content_data.get("text")
                    if not text_value:
                        raise serializers.ValidationError(
                            "Text content cannot be empty."
                        )
                    content_kwargs["text"] = text_value
                elif content_type == "image":
                    image_value = content_data.get("image")
                    if not image_value:
                        raise serializers.ValidationError(
                            "Image content cannot be empty."
                        )
                    content_kwargs["image"] = image_value

                Content.objects.create(**content_kwargs)

            if not isinstance(answer_options_data, list):
                raise serializers.ValidationError("Answer options must be a list.")

            if len(answer_options_data) == 0:
                raise serializers.ValidationError(
                    "At least one answer option is required."
                )

            has_correct_answer = any(
                answer.get("is_correct", False) for answer in answer_options_data
            )
            if not has_correct_answer:
                raise serializers.ValidationError(
                    "At least one answer option must be marked as correct."
                )

            for answer_data in answer_options_data:
                option_type = answer_data.get("option_type", "text")

                if option_type not in ["text", "image"]:
                    raise serializers.ValidationError(
                        f"Unsupported option type: {option_type}"
                    )

                answer_kwargs = {
                    "question": instance,
                    "is_correct": answer_data.get("is_correct", False),
                    "option_type": option_type,
                }

                if option_type == "text":
                    text_value = answer_data.get("text")
                    if not text_value:
                        raise serializers.ValidationError(
                            "Text answer option cannot be empty."
                        )
                    answer_kwargs["text"] = text_value
                elif option_type == "image":
                    image_value = answer_data.get("image")
                    if not image_value:
                        raise serializers.ValidationError(
                            "Image answer option cannot be empty."
                        )
                    answer_kwargs["image"] = image_value

                AnswerOption.objects.create(**answer_kwargs)

            return instance


class ShortTestSerializer(serializers.ModelSerializer):
    is_finished = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Test
        fields = [
            "id",
            "title",
            "shuffle_questions",
            "description",
            "test_type",
            "is_finished",
        ]
        read_only_fields = [
            "id",
            "title",
            "shuffle_questions",
            "description",
            "test_type",
            "is_finished",
        ]

    def get_is_finished(self, obj):
        user = self.context.get("request").user
        # print(user)
        if user is None:
            return False
        if user.is_parent:
            child_id = self.context.get("child_id")
            if child_id:
                return obj.results.filter(
                    child__id=child_id, is_finished=True, test=obj
                ).exists()
            else:
                raise serializers.ValidationError(
                    "Child ID is required for parent users."
                )
        elif user.is_student:
            return obj.results.filter(user=user, is_finished=True, test=obj).exists()
        else:
            return False


class ShortTestResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = TestResult
        fields = [
            "attempt_number",
            "is_finished",
            "score",
            "total_questions",
            "correct_answers",
        ]
        read_only_fields = [
            "attempt_number",
            "is_finished",
            "score",
            "total_questions",
            "correct_answers",
        ]


class TestSerializer(serializers.ModelSerializer):
    questions = TestQuestionSerializer(many=True, read_only=True)
    is_finished = serializers.SerializerMethodField()
    score_percentage = serializers.SerializerMethodField()
    test_results = serializers.SerializerMethodField()

    def get_test_results(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        user = request.user
        if user.is_parent:
            child_id = self.context.get("child_id")
            if not child_id:
                raise serializers.ValidationError(
                    "Child ID is required for parent users."
                )
            results = obj.results.filter(child__id=child_id)
        elif user.is_student:
            results = obj.results.filter(user=user)
        else:
            return []

        return ShortTestResultSerializer(results, many=True).data

    def get_is_finished(self, obj):
        user = self.context.get("request").user
        if user is None:
            return False
        if user.is_parent:
            print(self.context)
            child_id = self.context.get("child_id")
            if child_id:
                return obj.results.filter(
                    child__id=child_id, is_finished=True, test=obj
                ).exists()
            else:
                raise serializers.ValidationError(
                    "Child ID is required for parent users."
                )
        elif user.is_student:
            return obj.results.filter(user=user, is_finished=True, test=obj).exists()
        else:
            return False

    def get_score_percentage(self, obj):
        user = self.context.get("request").user
        if user.is_parent:
            child_id = self.context.get("child_id")
            if child_id:
                result = obj.results.filter(child__id=child_id, test=obj).first()
            else:
                raise serializers.ValidationError(
                    "Child ID is required for parent users."
                )
        elif user.is_student:
            result = obj.results.filter(user=user, test=obj).first()
        else:
            return None

        if result and result.total_questions > 0:
            return (result.correct_answers / result.total_questions) * 100
        return 0.0

    class Meta:
        model = Test
        fields = "__all__"


class TestAnswerSerializer(serializers.ModelSerializer):
    question = TestQuestionSerializer(read_only=True)
    answer_option = AnswerOptionSerializer(read_only=True)

    class Meta:
        model = TestAnswer
        fields = "__all__"


class TestResultSerializer(serializers.ModelSerializer):
    test_answers = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = "__all__"

    @extend_schema_field(TestAnswerSerializer(many=True))
    def get_test_answers(self, obj):
        # Access context request
        request = self.context.get("request")
        if not request:
            return []

        # Determine user or child
        if obj.user:
            answers = TestAnswer.objects.filter(question__test=obj.test, user=obj.user)
        else:
            answers = TestAnswer.objects.filter(
                question__test=obj.test, child=obj.child
            )

        return TestAnswerSerializer(answers, many=True, context=self.context).data


class FullAnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        exclude = ["question"]

    def validate(self, data):
        if data.get("option_type") == "text":
            if not data.get("text"):
                raise serializers.ValidationError("Text is required for text option.")
            if data.get("image"):
                raise serializers.ValidationError(
                    "Image must be empty for text option."
                )
        elif data.get("option_type") == "image":
            if not data.get("image"):
                raise serializers.ValidationError("Image is required for image option.")
            if data.get("text"):
                raise serializers.ValidationError(
                    "Text must be empty for image option."
                )
        else:
            raise serializers.ValidationError("Invalid option_type.")
        return data


class FullContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        exclude = ["question"]

    def validate(self, data):
        if data.get("content_type") == "text":
            if not data.get("text"):
                raise serializers.ValidationError("Text is required for text content.")
            if data.get("image"):
                raise serializers.ValidationError(
                    "Image must be empty for text content."
                )
        elif data.get("content_type") == "image":
            if not data.get("image"):
                raise serializers.ValidationError(
                    "Image is required for image content."
                )
            if data.get("text"):
                raise serializers.ValidationError(
                    "Text must be empty for image content."
                )
        else:
            raise serializers.ValidationError("Invalid content_type.")
        return data


class FullQuestionCreateSerializer(serializers.ModelSerializer):
    contents = FullContentSerializer(many=True, required=False)
    answer_options = FullAnswerOptionSerializer(many=True, required=False)

    class Meta:
        model = Question
        exclude = ["test"]

    def create(self, validated_data):
        contents_data = validated_data.pop("contents", [])
        answers_data = validated_data.pop("answer_options", [])
        test = self.context.get("test")

        if 'order' not in validated_data:
            order = len(test.questions.all())+1
            validated_data['order'] = order
        question = Question.objects.create(test=test, **validated_data)

        if contents_data:
            for content in contents_data:
                Content.objects.create(question=question, **content)

        if answers_data:
            for answer in answers_data:
                AnswerOption.objects.create(question=question, **answer)

        return question


class FullTestCreateSerializer(serializers.ModelSerializer):
    questions = FullQuestionCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Test
        fields = [
            "title",
            "shuffle_questions",
            "description",
            "test_type",
            "order",
            "questions",
            "category"
        ]

    def create(self, validated_data):
        print(validated_data)
        questions_data = validated_data.pop("questions", [])
        if isinstance(questions_data, dict):
            questions_data = [questions_data]
        test = Test.objects.create(**validated_data)

        for question_data in questions_data:
            contents_data = question_data.pop("contents", [])
            answers_data = question_data.pop("answer_options", [])
            question = Question.objects.create(test=test, **question_data)

            for content in contents_data:
                Content.objects.create(question=question, **content)

            for answer in answers_data:
                AnswerOption.objects.create(question=question, **answer)

        return test

class ImageOrURLField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith(("http://", "https://")):
            return data
        return super().to_internal_value(data)

class FullAnswerOptionUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image = ImageOrURLField(required=False, allow_null=True)

    class Meta:
        model = AnswerOption
        exclude = ["question"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr=="image" and "storage.yandexcloud.kz/protosedu" in value:
                continue
            setattr(instance, attr, value)
        print(validated_data)
        instance.save()
        return instance

    def validate(self, data):
        option_type = data.get(
            "option_type", getattr(self.instance, "option_type", None)
        )
        text = data.get("text", getattr(self.instance, "text", None))
        image = data.get("image", getattr(self.instance, "image", None))

        if option_type == "text":
            if not text:
                raise serializers.ValidationError("Text is required for text option.")
        elif option_type == "image":
            if not image:
                raise serializers.ValidationError("Image is required for image option.")
        return data


class FullContentUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Content
        exclude = ["question"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate(self, data):
        content_type = data.get(
            "content_type", getattr(self.instance, "content_type", None)
        )
        text = data.get("text", getattr(self.instance, "text", None))
        image = data.get("image", getattr(self.instance, "image", None))

        if content_type == "text":
            if not text:
                raise serializers.ValidationError("Text is required for text content.")
        elif content_type == "image":
            if not image:
                raise serializers.ValidationError(
                    "Image is required for image content."
                )
        return data


class FullQuestionUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contents = FullContentUpdateSerializer(many=True, required=False)
    answer_options = FullAnswerOptionUpdateSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ["id", "title", "order", "contents", "answer_options"]

    def update(self, instance, validated_data):
        contents_data = validated_data.pop("contents", [])
        options_data = validated_data.pop("answer_options", [])

        print(f"contents_data: {contents_data}")
        print(f"options_data: {options_data}")

        # --- Update question fields ---
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # --- Handle Contents (if any) ---
        for content_data in contents_data:
            content_id = content_data.get("id")
            if content_id:
                content_instance = instance.contents.filter(id=content_id).first()
                if content_instance:
                    serializer = FullContentUpdateSerializer(
                        content_instance, data=content_data, partial=True
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    continue
            Content.objects.create(question=instance, **content_data)

        # --- Handle Answer Options (if any) ---
        for option_data in options_data:
            option_id = option_data.get("id")
            if option_id:
                option_instance = instance.answer_options.filter(id=option_id).first()
                if option_instance:
                    serializer = FullAnswerOptionUpdateSerializer(
                        option_instance, data=option_data, partial=True
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    continue
            AnswerOption.objects.create(question=instance, **option_data)

        return instance


class FullTestUpdateSerializer(serializers.ModelSerializer):
    questions = FullQuestionUpdateSerializer(many=True, write_only=True)

    class Meta:
        model = Test
        fields = [
            "title",
            "shuffle_questions",
            "description",
            "test_type",
            "order",
            "questions",
        ]

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions")

        # Update main test fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        existing_questions = {q.id: q for q in instance.questions.all()}
        seen_question_ids = []

        for q_data in questions_data:
            q_id = q_data.get("id")
            if q_id and q_id in existing_questions:
                question_instance = existing_questions[q_id]
                serializer = FullQuestionUpdateSerializer(
                    question_instance,
                    data=q_data,
                    context=self.context,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                seen_question_ids.append(q_id)
            else:
                q_data["test"] = instance.id
                serializer = FullQuestionUpdateSerializer(
                    data=q_data, context=self.context
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(test=instance)

        # Optional: remove questions that were deleted
        # instance.questions.exclude(id__in=seen_question_ids).delete()

        return instance


class TestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCategory
        fields = [
            "id",
            "name",
            "is_mandatory",
            "is_profile",
            "language",
            "test_type",
            "image",
        ]
