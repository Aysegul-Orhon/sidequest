from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Season(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class TimeOfDay(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name


class SideQuest(models.Model):
    LOCATION_CHOICES = [
        ("indoor", "Indoor"),
        ("outdoor", "Outdoor"),
        ("both", "Both"),
    ]
    COST_CHOICES = [
        ("free", "Free"),
        ("cheap", "Cheap"),
        ("medium", "Medium"),
        ("pricey", "Pricey"),
    ]
    SOCIAL_CHOICES = [
        ("solo", "Solo"),
        ("group", "With others"),
        ("either", "Either"),
    ]
    EFFORT_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]
    DURATION_CHOICES = [
        ("short", "Short (< 2 hours)"),
        ("medium", "Medium"),
        ("long", "Long (days/weeks)"),
    ]
    ACTIVITY_TYPE_CHOICES = [
        ("creative", "Creative"),
        ("writing", "Writing"),
        ("research", "Research"),
        ("reading", "Reading"),
        ("media", "Media"),
        ("physical", "Physical"),
        ("social", "Social"),
        ("outdoor", "Outdoor"),
        ("home", "Home"),
        ("skill", "Skill"),
        ("practical", "Practical"),
        ("food", "Food"),
    ]

    title = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    location_type = models.CharField(max_length=10, choices=LOCATION_CHOICES)
    cost_level = models.CharField(max_length=10, choices=COST_CHOICES)
    social_type = models.CharField(max_length=10, choices=SOCIAL_CHOICES)
    seasons = models.ManyToManyField(Season, related_name="sidequests", blank=True)
    effort_level = models.CharField(max_length=10, choices=EFFORT_CHOICES)
    duration_level = models.CharField(max_length=20, choices=DURATION_CHOICES)
    times_of_day = models.ManyToManyField(TimeOfDay, related_name="sidequests", blank=True)
    categories = models.ManyToManyField(Category, related_name="sidequests")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserQuest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sidequest = models.ForeignKey(SideQuest, on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    saved_at = models.DateTimeField(auto_now_add=True)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "sidequest")

    def __str__(self):
        return f"{self.user} - {self.sidequest}"


class UserPreference(models.Model):
    SOCIAL_PREF_CHOICES = [
        ("solo", "Solo"),
        ("group", "With others"),
    ]
    LOCATION_PREF_CHOICES = [
        ("indoor", "Indoor"),
        ("outdoor", "Outdoor"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    location_type = models.CharField(
        max_length=10,
        choices=LOCATION_PREF_CHOICES,
        null=True,
        blank=True,
    )
    cost_level = models.CharField(
        max_length=10,
        choices=SideQuest.COST_CHOICES,
        null=True,
        blank=True,
    )
    social_type = models.CharField(
        max_length=10,
        choices=SOCIAL_PREF_CHOICES,
        null=True,
        blank=True,
    )
    effort_level = models.CharField(
        max_length=10,
        choices=SideQuest.EFFORT_CHOICES,
        null=True,
        blank=True,
    )
    duration_level = models.CharField(
        max_length=10,
        choices=SideQuest.DURATION_CHOICES,
        null=True,
        blank=True,
    )
    categories = models.ManyToManyField(Category, blank=True)
    seasons = models.ManyToManyField(Season, blank=True)
    times_of_day = models.ManyToManyField(TimeOfDay, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} preferences"
