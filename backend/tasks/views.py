from collections import Counter
import random

from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Category, Season, SideQuest, TimeOfDay, UserPreference, UserQuest
from .serializers import SideQuestSerializer, UserPreferenceSerializer, UserQuestSerializer


class SideQuestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only catalog endpoint.
    Supports filtering with query params, e.g.:
    /api/sidequests/?location_type=indoor&cost_level=free
    """
    serializer_class = SideQuestSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = SideQuest.objects.all().order_by("-created_at")
        p = self.request.query_params

        if "activity_type" in p:
            qs = qs.filter(activity_type=p["activity_type"])
        if "location_type" in p:
            qs = qs.filter(location_type=p["location_type"])
        if "cost_level" in p:
            qs = qs.filter(cost_level=p["cost_level"])
        if "social_type" in p:
            qs = qs.filter(social_type=p["social_type"])
        if "effort_level" in p:
            qs = qs.filter(effort_level=p["effort_level"])
        if "duration_level" in p:
            qs = qs.filter(duration_level=p["duration_level"])

        if "category" in p:
            qs = qs.filter(categories__name__iexact=p["category"])
        if "season" in p:
            qs = qs.filter(seasons__name__iexact=p["season"])
        if "time_of_day" in p:
            qs = qs.filter(times_of_day__name__iexact=p["time_of_day"])

        return qs.distinct()


class UserQuestViewSet(viewsets.ModelViewSet):
    """The logged-in user's saved quests."""
    serializer_class = UserQuestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserQuest.objects.filter(user=self.request.user).order_by("-saved_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            serializer.save(user=request.user)
        except IntegrityError:
            return Response(
                {"detail": "You already saved this side quest."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        done = serializer.validated_data.get("done", None)

        if done is True:
            serializer.save(done_at=timezone.now())
        elif done is False:
            serializer.save(done_at=None)
        else:
            serializer.save()


class UserPreferenceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref)
        return Response(serializer.data)

    def update(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def options(request):
    data = {
        # Catalog choices: these describe SideQuest objects.
        "activity_types": [key for key, _ in SideQuest.ACTIVITY_TYPE_CHOICES],
        "location_types": [key for key, _ in SideQuest.LOCATION_CHOICES],
        "cost_levels": [key for key, _ in SideQuest.COST_CHOICES],
        "social_types": [key for key, _ in SideQuest.SOCIAL_CHOICES],
        "effort_levels": [key for key, _ in SideQuest.EFFORT_CHOICES],
        "duration_levels": [key for key, _ in SideQuest.DURATION_CHOICES],

        # Preference choices: these intentionally exclude "both" / "either".
        # Empty/null preference means "I don't care".
        "preference_location_types": [key for key, _ in UserPreference.LOCATION_PREF_CHOICES],
        "preference_social_types": [key for key, _ in UserPreference.SOCIAL_PREF_CHOICES],

        # Many-to-many tag tables.
        "categories": list(Category.objects.values_list("name", flat=True).order_by("name")),
        "seasons": list(Season.objects.values_list("name", flat=True).order_by("name")),
        "times_of_day": list(TimeOfDay.objects.values_list("name", flat=True).order_by("name")),
    }
    return Response(data)


def _matches_location(quest_location, preferred_location):
    """If user prefers indoor, a quest marked both should still match."""
    return bool(preferred_location) and quest_location in (preferred_location, "both")


def _matches_social(quest_social, preferred_social):
    """If user prefers solo/group, a quest marked either should still match."""
    return bool(preferred_social) and quest_social in (preferred_social, "either")


def _diversify_by_activity_type(scored_items, limit):
    """
    Return up to `limit` scored items while avoiding the same activity_type
    back-to-back whenever possible.

    Each item is (score, quest, reasons). The input should already be ordered
    by relevance. This function preserves relevance as much as possible: it
    always picks the highest-ranked remaining item whose activity type differs
    from the previous one; if that is impossible, it picks the highest-ranked
    remaining item.
    """
    remaining = list(scored_items)
    final = []
    last_activity_type = None

    while remaining and len(final) < limit:
        chosen_index = 0

        for index, item in enumerate(remaining):
            quest = item[1]
            if quest.activity_type != last_activity_type:
                chosen_index = index
                break

        chosen = remaining.pop(chosen_index)
        final.append(chosen)
        last_activity_type = chosen[1].activity_type

    return final


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def suggestions(request):
    user = request.user
    pref, _ = UserPreference.objects.get_or_create(user=user)

    saved_sidequest_ids = UserQuest.objects.filter(user=user).values_list("sidequest_id", flat=True)

    candidate_quests = (
        SideQuest.objects
        .exclude(id__in=saved_sidequest_ids)
        .prefetch_related("categories", "seasons", "times_of_day")
        .order_by("-created_at")
    )

    user_quests = (
        UserQuest.objects
        .filter(user=user)
        .select_related("sidequest")
        .prefetch_related("sidequest__categories")
    )

    history_category_names = []
    for user_quest in user_quests:
        for category in user_quest.sidequest.categories.all():
            history_category_names.append(category.name)

    history_counts = Counter(history_category_names)

    pref_categories = set(pref.categories.values_list("name", flat=True))
    pref_seasons = set(pref.seasons.values_list("name", flat=True))
    pref_times = set(pref.times_of_day.values_list("name", flat=True))

    weights = {
        "location": 3,
        "cost": 3,
        "social": 2,
        "effort": 2,
        "duration": 3,
        "category": 2,
        "season": 1,
        "time": 1,
        "history_category": 1,
    }

    scored = []

    for quest in candidate_quests:
        score = 0
        reasons = []

        if _matches_location(quest.location_type, pref.location_type):
            score += weights["location"]
            reasons.append(f"location +{weights['location']}")

        if pref.cost_level and quest.cost_level == pref.cost_level:
            score += weights["cost"]
            reasons.append(f"cost +{weights['cost']}")

        if _matches_social(quest.social_type, pref.social_type):
            score += weights["social"]
            reasons.append(f"social +{weights['social']}")

        if pref.effort_level and quest.effort_level == pref.effort_level:
            score += weights["effort"]
            reasons.append(f"effort +{weights['effort']}")

        if pref.duration_level and quest.duration_level == pref.duration_level:
            score += weights["duration"]
            reasons.append(f"duration +{weights['duration']}")

        quest_categories = {c.name for c in quest.categories.all()}
        quest_seasons = {s.name for s in quest.seasons.all()}
        quest_times = {t.name for t in quest.times_of_day.all()}

        category_overlap = quest_categories & pref_categories
        season_overlap = quest_seasons & pref_seasons
        time_overlap = quest_times & pref_times

        if category_overlap:
            points = weights["category"] * len(category_overlap)
            score += points
            reasons.append(f"categories {', '.join(sorted(category_overlap))} +{points}")

        if season_overlap:
            points = weights["season"] * len(season_overlap)
            score += points
            reasons.append(f"seasons {', '.join(sorted(season_overlap))} +{points}")

        if time_overlap:
            points = weights["time"] * len(time_overlap)
            score += points
            reasons.append(f"times {', '.join(sorted(time_overlap))} +{points}")

        history_points = 0
        for category_name in quest_categories:
            history_points += weights["history_category"] * history_counts.get(category_name, 0)

        if history_points:
            score += history_points
            reasons.append(f"similar to saved quests +{history_points}")

        scored.append((score, quest, reasons))

    # Sort once, AFTER all quests have been scored.
    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)

    try:
        limit = int(request.query_params.get("limit", 20))
    except ValueError:
        limit = 20
    limit = max(1, min(limit, 100))

    seed = request.query_params.get("seed")

    if seed:
        # Controlled variety: only shuffle a high-scoring pool, not the full catalog.
        pool_size = min(len(scored), max(limit * 3, limit))
        pool = scored[:pool_size]
        rng = random.Random(None if seed == "random" else seed)
        rng.shuffle(pool)
        final = _diversify_by_activity_type(pool, limit)
    else:
        final = _diversify_by_activity_type(scored, limit)

    quests = [quest for score, quest, reasons in final]
    data = SideQuestSerializer(quests, many=True).data

    # Attach each score/reason to the exact same quest it came from.
    for item, (score, quest, reasons) in zip(data, final):
        item["score"] = score
        item["score_reasons"] = reasons

    return Response({
        "limit": limit,
        "seed": seed,
        "results": data,
    })
