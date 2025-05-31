from rest_framework import serializers
from .models import Test, Question, Content, AnswerOption, TestAnswer, TestResult


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


class QuestionSerializer(serializers.ModelSerializer):
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
    questions = QuestionSerializer(many=True, read_only=True)
    is_finished = serializers.SerializerMethodField()
    score_percentage = serializers.SerializerMethodField()

    def get_is_finished(self, obj):
        user = self.context.get("request").user
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
    question = QuestionSerializer(read_only=True)
    answer_option = AnswerOptionSerializer(read_only=True)

    class Meta:
        model = TestAnswer
        fields = "__all__"


class TestResultSerializer(serializers.ModelSerializer):
    test_answers = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = "__all__"

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
