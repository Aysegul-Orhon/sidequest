from django.urls import path
from . import auth_views

urlpatterns = [
    path("register/", auth_views.register),
    path("login/", auth_views.login),
    path("logout/", auth_views.logout),
    path("me/", auth_views.me),
]
