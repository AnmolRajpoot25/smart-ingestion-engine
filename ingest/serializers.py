from rest_framework import serializers

from .models import (
    IngestionBatch,
    EmissionRecord,
    AuditEvent,
    ParseError,
)

# INGESTION BATCH


class IngestionBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngestionBatch

        fields = "__all__"

# EMISSION RECORD


class EmissionRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmissionRecord

        fields = "__all__"



# AUDIT EVENT


class AuditEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuditEvent

        fields = "__all__"



# PARSE ERROR


class ParseErrorSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParseError

        fields = "__all__"