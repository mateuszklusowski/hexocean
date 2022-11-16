from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("images", views.ImageListViewSet, basename="images")

app_name = "core"

urlpatterns = [
    path("", include(router.urls)),
    path(
        "images/<int:image_pk>/create/",
        views.CreateBinaryLinkView.as_view(),
        name="create-link",
    ),
    path(
        "images/<uuid:binary_pk>/",
        views.RetrieveBinaryLinkView.as_view(),
        name="get-binary-link",
    ),
]
