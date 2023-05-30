from django.conf.urls import url
from django.urls import path, include


from rest_framework.routers import DefaultRouter
from . import views
from django.conf import settings

router = DefaultRouter()
router.register("space", views.SpaceViewSet)
router.register("label", views.LabelViewSet)
router.register("post", views.PostViewSet)
router.register("annotation", views.AnnotationView, basename="annotation")
router.register("wikidata-search", views.WikidataViewSet, basename="wikidata-view")


app_name = "feed"

urlpatterns = [
    path('explore/', views.explore, name='explore'),
    path("", include(router.urls)),
]

