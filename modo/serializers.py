from rest_framework import serializers
from .models import Test, Question, Content, AnswerOption




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
            if key=="text":
                Content.objects.create(
                    question=instance,
                    content_type=key,
                    text=contents[key],
                )
            else:
                Content.objects.create(
                    question=instance,
                    content_type=key,
                    image=contents[key]
                )
        
        for answer in answers:
            AnswerOption.objects.create(
                question=instance,
                text=answer["text"],
                is_correct=answer["is_correct"]
            )


class TestSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    class Meta:
        model = Test
        fields = "__all__"