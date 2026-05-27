from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ingest.models import (
    EmissionRecord,
    IngestionBatch,
    AuditEvent,
    ParseError,
)

from ingest.serializers import (
    EmissionRecordSerializer,
    IngestionBatchSerializer,
    AuditEventSerializer,
    ParseErrorSerializer,
)


# =========================================================
# RECORD LIST API
# =========================================================

class RecordListAPIView(APIView):

    def get(self, request):

        records = EmissionRecord.objects.all().order_by("-created_at")

        serializer = EmissionRecordSerializer(records, many=True)

        return Response(serializer.data)


# =========================================================
# FLAGGED RECORDS
# =========================================================

class FlaggedRecordsAPIView(APIView):

    def get(self, request):

        records = EmissionRecord.objects.filter(
            review_status=EmissionRecord.STATUS_FLAGGED
        )

        serializer = EmissionRecordSerializer(records, many=True)

        return Response(serializer.data)


# =========================================================
# APPROVE RECORD
# =========================================================

class ApproveRecordAPIView(APIView):

    def post(self, request, record_id):

        try:
            record = EmissionRecord.objects.get(id=record_id)

        except EmissionRecord.DoesNotExist:

            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user, _ = User.objects.get_or_create(
            username="review_analyst"
        )

        record.review_status = EmissionRecord.STATUS_APPROVED

        record.reviewed_by = user

        record.reviewed_at = timezone.now()

        record.is_locked = True

        record.save()

        AuditEvent.objects.create(
            record=record,
            actor=user,
            action=AuditEvent.ACTION_APPROVED,
            diff={},
            note="Record approved by analyst",
        )

        return Response({
            "message": "Record approved"
        })


# =========================================================
# REJECT RECORD
# =========================================================

class RejectRecordAPIView(APIView):

    def post(self, request, record_id):

        try:
            record = EmissionRecord.objects.get(id=record_id)

        except EmissionRecord.DoesNotExist:

            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user, _ = User.objects.get_or_create(
            username="review_analyst"
        )

        record.review_status = EmissionRecord.STATUS_REJECTED

        record.reviewed_by = user

        record.reviewed_at = timezone.now()

        record.save()

        AuditEvent.objects.create(
            record=record,
            actor=user,
            action=AuditEvent.ACTION_REJECTED,
            diff={},
            note="Record rejected by analyst",
        )

        return Response({
            "message": "Record rejected"
        })


# =========================================================
# INGESTION BATCHES
# =========================================================

class BatchListAPIView(APIView):

    def get(self, request):

        batches = IngestionBatch.objects.all().order_by("-ingested_at")

        serializer = IngestionBatchSerializer(batches, many=True)

        return Response(serializer.data)


# =========================================================
# PARSE ERRORS
# =========================================================

class ParseErrorListAPIView(APIView):

    def get(self, request):

        errors = ParseError.objects.all().order_by("-created_at")

        serializer = ParseErrorSerializer(errors, many=True)

        return Response(serializer.data)


# =========================================================
# AUDIT TRAIL
# =========================================================

class AuditTrailAPIView(APIView):

    def get(self, request, record_id):

        events = AuditEvent.objects.filter(
            record_id=record_id
        ).order_by("-timestamp")

        serializer = AuditEventSerializer(events, many=True)

        return Response(serializer.data)