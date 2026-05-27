from django.urls import path

from .views import (
    RecordListAPIView,
    FlaggedRecordsAPIView,
    ApproveRecordAPIView,
    RejectRecordAPIView,
    BatchListAPIView,
    ParseErrorListAPIView,
    AuditTrailAPIView,
)

urlpatterns = [

    path(
        "records/",
        RecordListAPIView.as_view(),
    ),

    path(
        "records/flagged/",
        FlaggedRecordsAPIView.as_view(),
    ),

    path(
        "records/<uuid:record_id>/approve/",
        ApproveRecordAPIView.as_view(),
    ),

    path(
        "records/<uuid:record_id>/reject/",
        RejectRecordAPIView.as_view(),
    ),

    path(
        "batches/",
        BatchListAPIView.as_view(),
    ),

    path(
        "errors/",
        ParseErrorListAPIView.as_view(),
    ),

    path(
        "audit/<uuid:record_id>/",
        AuditTrailAPIView.as_view(),
    ),
]