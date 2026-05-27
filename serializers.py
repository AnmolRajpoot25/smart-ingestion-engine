from rest_framework import serializers
from .models import (
    Tenant, TenantMembership, IngestionBatch,
    EmissionRecord, AuditEvent, ParseError
)


# ─────────────────────────────────────────────
# BATCH SERIALIZERS
# ─────────────────────────────────────────────

class IngestionBatchSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = IngestionBatch
        fields = [
            "id", "source_type", "status", "row_count", "error_count",
            "ingested_at", "completed_at", "raw_file_name", "uploaded_by_name", "notes"
        ]

    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username if obj.uploaded_by else None


# ─────────────────────────────────────────────
# EMISSION RECORD SERIALIZERS
# ─────────────────────────────────────────────

class EmissionRecordSerializer(serializers.ModelSerializer):
    scope_label = serializers.SerializerMethodField()
    category_label = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EmissionRecord
        fields = [
            "id", "scope", "scope_label", "category", "category_label",
            "source_type", "activity_date", "period_start", "period_end",
            "raw_quantity", "raw_unit", "normalized_quantity", "normalized_unit",
            "emission_factor", "emission_factor_source", "co2e_kg",
            "location_code", "location_label", "vendor_or_carrier", "description",
            "source_row_id", "review_status", "reviewed_by_name", "reviewed_at",
            "review_note", "is_edited", "is_locked", "flag_reason",
            "created_at", "updated_at",
        ]

    def get_scope_label(self, obj):
        return dict(EmissionRecord.SCOPES).get(obj.scope, "")

    def get_category_label(self, obj):
        return dict(EmissionRecord.CATEGORIES).get(obj.category, obj.category)

    def get_reviewed_by_name(self, obj):
        return obj.reviewed_by.get_full_name() or obj.reviewed_by.username if obj.reviewed_by else None


class EmissionRecordUpdateSerializer(serializers.ModelSerializer):
    """Restricted serializer for analyst edits — prevents touching locked or audit fields."""

    class Meta:
        model = EmissionRecord
        fields = ["review_status", "review_note", "description", "location_label"]

    def validate(self, attrs):
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError("Record is locked for audit and cannot be edited.")
        return attrs


# ─────────────────────────────────────────────
# AUDIT TRAIL SERIALIZER
# ─────────────────────────────────────────────

class AuditEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = ["id", "action", "diff", "timestamp", "note", "actor_name"]

    def get_actor_name(self, obj):
        return obj.actor.get_full_name() or obj.actor.username if obj.actor else "system"


# ─────────────────────────────────────────────
# PARSE ERROR SERIALIZER
# ─────────────────────────────────────────────

class ParseErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParseError
        fields = ["id", "row_index", "raw_content", "error_message", "created_at"]