from rest_framework import serializers
from .models import League, LeagueGroup, LeagueGroupParticipant


# class LeagueSerializer(serializers.ModelSerializer):
#     number_of_groups = serializers.IntegerField(read_only=True)

#     class Meta:
#         model = League
#         fields = "__all__"
#         read_only_fields = ("number_of_groups",)


class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = (
            "id",
            "name",
            "rank",
            "icon",
            "max_players",
            "promotions_rate",
            "demotions_rate",
        )
        read_only_fields = (
            "id",
            "rank",
            "icon",
            "max_players",
            "promotions_rate",
            "demotions_rate",
        )


class LeagueGroupSerializer(serializers.ModelSerializer):
    league = LeagueSerializer(read_only=True)

    class Meta:
        model = LeagueGroup
        fields = "__all__"
        read_only_fields = ("league",)


class LeagueGroupParticipantSerializer(serializers.ModelSerializer):
    league_group = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = LeagueGroupParticipant
        fields = "__all__"
        read_only_fields = ("league_group",)
