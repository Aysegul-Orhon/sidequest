from django.contrib import admin
from .models import Category, Season, TimeOfDay, SideQuest, UserQuest, UserPreference

admin.site.register(Category)
admin.site.register(Season)
admin.site.register(TimeOfDay)
admin.site.register(SideQuest)
admin.site.register(UserQuest)
admin.site.register(UserPreference)

