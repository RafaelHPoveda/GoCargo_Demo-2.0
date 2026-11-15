from django.urls import include, path
from drf_spectacular.views import SpectacularJSONAPIView

from config.api_docs import api_docs

urlpatterns = [
    path("api/docs/", api_docs, name="api-docs"),
    path("api/schema/", SpectacularJSONAPIView.as_view(), name="openapi-schema"),
    path("api/", include("apps.branches.presentation.urls")),
    path("api/", include("apps.shipments.presentation.urls")),
]
