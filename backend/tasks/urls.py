from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SideQuestViewSet, UserQuestViewSet, UserPreferenceViewSet, options, suggestions

router = DefaultRouter()
router.register("sidequests", SideQuestViewSet, basename="sidequest")
router.register("my-quests", UserQuestViewSet, basename="userquest")

urlpatterns = [
    path("preferences/", UserPreferenceViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update"})),
    path("", include(router.urls)),
    path("options/", options),
    path("suggestions/", suggestions),
]


