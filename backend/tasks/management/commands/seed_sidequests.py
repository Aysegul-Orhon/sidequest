import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tasks.models import SideQuest, Category, Season, TimeOfDay


def normalize_tag_name(name):
    """Keep catalog tag names consistent so Art/art do not become separate options later."""
    return str(name).strip().lower()


class Command(BaseCommand):
    help = "Seed the database with SideQuest catalog items from JSON."

    required_fields = [
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
    ]

    def handle(self, *args, **options):
        file_path = Path(settings.BASE_DIR) / "tasks" / "seed_data" / "sidequests.json"

        if not file_path.exists():
            raise CommandError(f"Seed file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            quests = json.load(f)

        created_count = 0
        updated_count = 0

        for index, item in enumerate(quests, start=1):
            missing = [field for field in self.required_fields if field not in item]
            if missing:
                raise CommandError(
                    f"Item #{index} ({item.get('title', 'NO TITLE')}) is missing fields: {', '.join(missing)}"
                )

            if not item["categories"]:
                raise CommandError(
                    f"Item #{index} ({item['title']}) must have at least one category."
                )

            sidequest, created = SideQuest.objects.update_or_create(
                title=item["title"],
                defaults={
                    "activity_type": item["activity_type"],
                    "location_type": item["location_type"],
                    "cost_level": item["cost_level"],
                    "social_type": item["social_type"],
                    "effort_level": item["effort_level"],
                    "duration_level": item["duration_level"],
                },
            )

            categories = []
            for raw_name in item.get("categories", []):
                name = normalize_tag_name(raw_name)
                category, _ = Category.objects.get_or_create(name=name)
                categories.append(category)
            sidequest.categories.set(categories)

            seasons = []
            for raw_name in item.get("seasons", []):
                name = normalize_tag_name(raw_name)
                season, _ = Season.objects.get_or_create(name=name)
                seasons.append(season)
            sidequest.seasons.set(seasons)

            times = []
            for raw_name in item.get("times_of_day", []):
                name = normalize_tag_name(raw_name)
                time, _ = TimeOfDay.objects.get_or_create(name=name)
                times.append(time)
            sidequest.times_of_day.set(times)

            if created:
                created_count += 1
            else:
                updated_count += 1
        
                # Remove old user-facing category that we no longer want.
        old_home = Category.objects.filter(name="home").first()
        if old_home:
            for pref in old_home.userpreference_set.all():
                pref.categories.remove(old_home)

            for sidequest in old_home.sidequests.all():
                sidequest.categories.remove(old_home)

            old_home.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. Created {created_count}, updated {updated_count} sidequests."
            )
        )
