from django.conf.urls import url
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register("user", views.UserViewSet)

app_name = "user"

urlpatterns = [
    # path("register_form", views.register_form, name="register"),
    # path("register", views.register, name="register"),
    # path("login_form", views.login_form, name="login"),
    # path("login", views.login, name="login"),
    path("", views.index, name="main"),
    path("", include(router.urls)),
]
