from rest_framework import serializers
from .models import Test, Question, Content, AnswerOption, TestAnswer, TestResult
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


class TestSerializer(serializers.ModelSerializer):
    questions = TestQuestionSerializer(many=True, read_only=True)
    is_finished = serializers.SerializerMethodField()
    score_percentage = serializers.SerializerMethodField()

    def get_is_finished(self, obj):
        user = self.context.get("request").user
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
        test = self.context["test"]

        question = Question.objects.create(test=test, **validated_data)

        if contents_data:
            for content in contents_data:
                Content.objects.create(question=question, **content)

        if answers_data:
            for answer in answers_data:
                AnswerOption.objects.create(question=question, **answer)

        return question


class FullTestCreateSerializer(serializers.ModelSerializer):
    questions = FullQuestionCreateSerializer(many=True)

    class Meta:
        model = Test
        fields = ["title", "description", "test_type", "order", "questions"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
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


class FullAnswerOptionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        exclude = ["question"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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
            if image:
                raise serializers.ValidationError(
                    "Image must be empty for text option."
                )
        elif option_type == "image":
            if not image:
                raise serializers.ValidationError("Image is required for image option.")
            if text:
                raise serializers.ValidationError(
                    "Text must be empty for image option."
                )
        return data


class FullContentUpdateSerializer(serializers.ModelSerializer):
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
            if image:
                raise serializers.ValidationError(
                    "Image must be empty for text content."
                )
        elif content_type == "image":
            if not image:
                raise serializers.ValidationError(
                    "Image is required for image content."
                )
            if text:
                raise serializers.ValidationError(
                    "Text must be empty for image content."
                )
        return data


class FullQuestionUpdateSerializer(serializers.ModelSerializer):
    contents = FullContentUpdateSerializer(many=True, required=False)
    answer_options = FullAnswerOptionUpdateSerializer(many=True)

    class Meta:
        model = Question
        exclude = ["test"]

    def update(self, instance, validated_data):
        contents_data = validated_data.pop("contents", None)
        answers_data = validated_data.pop("answer_options", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # --- Update or create contents ---
        if contents_data is not None:
            existing_contents = {c.id: c for c in instance.contents.all()}
            seen_content_ids = []

            for content_data in contents_data:
                content_id = content_data.pop("id", None)

                if content_id and content_id in existing_contents:
                    content_instance = existing_contents[content_id]
                    serializer = FullContentUpdateSerializer(
                        content_instance, data=content_data, partial=True
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    seen_content_ids.append(content_id)
                else:
                    Content.objects.create(question=instance, **content_data)

            instance.contents.exclude(id__in=seen_content_ids).delete()

        # --- Update or create answer options ---
        existing_answers = {a.id: a for a in instance.answer_options.all()}
        seen_answer_ids = []

        for answer_data in answers_data:
            answer_id = answer_data.pop("id", None)

            if answer_id and answer_id in existing_answers:
                answer_instance = existing_answers[answer_id]
                serializer = FullAnswerOptionUpdateSerializer(
                    answer_instance, data=answer_data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                seen_answer_ids.append(answer_id)
            else:
                AnswerOption.objects.create(question=instance, **answer_data)

        instance.answer_options.exclude(id__in=seen_answer_ids).delete()

        return instance


class FullTestUpdateSerializer(serializers.ModelSerializer):
    questions = serializers.ListField(write_only=True)

    class Meta:
        model = Test
        fields = ["title", "description", "test_type", "order", "questions"]

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", [])

        # Update main test fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Get current question instances
        existing_questions = {q.id: q for q in instance.questions.all()}
        seen_question_ids = []

        for q_data in questions_data:
            q_id = q_data.pop("id", None)  # 💥 Prevent ID from leaking into create()
            contents = q_data.pop("contents", [])
            answers = q_data.pop("answer_options", [])

            if q_id and q_id in existing_questions:
                question = existing_questions[q_id]
                q_data["contents"] = contents
                q_data["answer_options"] = answers
                serializer = FullQuestionUpdateSerializer(
                    question, data=q_data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                seen_question_ids.append(q_id)
            else:
                question = Question.objects.create(test=instance, **q_data)
                for content in contents:
                    content.pop("id", None)  # just in case
                    Content.objects.create(question=question, **content)
                for answer in answers:
                    answer.pop("id", None)  # just in case
                    AnswerOption.objects.create(question=question, **answer)

        # Optionally delete removed questions
        # instance.questions.exclude(id__in=seen_question_ids).delete()

        return instance
