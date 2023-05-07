from django.conf.urls import url
from django.urls import path, include


from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("space", views.SpaceViewSet)
router.register("label", views.LabelViewSet)
router.register("post", views.PostViewSet)
router.register("annotation", views.CreateTextAnnotationView, basename="annotation")
router.register("image-annotation", views.CreateImagennotationView, basename="image-annotation")
router.register("wikidata-search", views.WikidataViewSet, basename="wikidata-view")


app_name = "meal"

urlpatterns = [
    path("", include(router.urls))
]

