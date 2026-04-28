from rest_framework import serializers
from .models import Category, Season, TimeOfDay, SideQuest, UserQuest, UserPreference


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["id", "name"]


class TimeOfDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeOfDay
        fields = ["id", "name"]


class SideQuestSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    times_of_day = TimeOfDaySerializer(many=True, read_only=True)

    class Meta:
        model = SideQuest
        fields = [
            "id",
            "title",
            "activity_type",
            "location_type",
            "cost_level",
            "social_type",
            "effort_level",
            "duration_level",
            "categories",
            "seasons",
            "times_of_day",
            "created_at",
        ]


class UserQuestSerializer(serializers.ModelSerializer):
    sidequest = SideQuestSerializer(read_only=True)

    sidequest_id = serializers.PrimaryKeyRelatedField(
        queryset=SideQuest.objects.all(),
        source="sidequest",
        write_only=True,
    )

    class Meta:
        model = UserQuest
        fields = ["id", "sidequest", "sidequest_id", "done", "saved_at", "done_at"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    categories = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Category.objects.all(), required=False
    )
    seasons = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=Season.objects.all(), required=False
    )
    times_of_day = serializers.SlugRelatedField(
        many=True, slug_field="name", queryset=TimeOfDay.objects.all(), required=False
    )

    class Meta:
        model = UserPreference
        fields = [
            "location_type",
            "cost_level",
            "social_type",
            "effort_level",
            "duration_level",
            "categories",
            "seasons",
            "times_of_day",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
