from django.urls import path

from .views import UploadIngestionAPIView

urlpatterns = [
    path(
        "upload/",
        UploadIngestionAPIView.as_view(),
        name="upload-ingestion"
    ),
]