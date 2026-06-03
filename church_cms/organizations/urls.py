from django.urls import path
from . import views

app_name = "organizations"

urlpatterns = [
    path("register/", views.register_church, name="register"),
]
