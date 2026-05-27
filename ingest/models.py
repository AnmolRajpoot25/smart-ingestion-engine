import uuid
from django.db import models
from django.contrib.auth.models import User


# =========================================================
# TENANT
# =========================================================

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    slug = models.SlugField(unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    ROLE_ANALYST = "analyst"
    ROLE_ADMIN = "admin"

    ROLES = [
        (ROLE_ANALYST, "Analyst"),
        (ROLE_ADMIN, "Admin"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="members"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLES,
        default=ROLE_ANALYST
    )

    class Meta:
        unique_together = ("user", "tenant")


# =========================================================
# INGESTION BATCH
# =========================================================

class IngestionBatch(models.Model):

    SOURCE_SAP = "sap"
    SOURCE_UTILITY = "utility"
    SOURCE_TRAVEL = "travel"

    SOURCES = [
        (SOURCE_SAP, "SAP"),
        (SOURCE_UTILITY, "Utility"),
        (SOURCE_TRAVEL, "Travel"),
    ]

    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    STATUSES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_DONE, "Done"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="batches"
    )

    source_type = models.CharField(
        max_length=20,
        choices=SOURCES
    )

    uploaded_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL
    )

    raw_file = models.FileField(
        upload_to="raw/%Y/%m/",
        null=True,
        blank=True
    )

    raw_file_name = models.CharField(
        max_length=512,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default=STATUS_PENDING
    )

    row_count = models.IntegerField(default=0)

    error_count = models.IntegerField(default=0)

    ingested_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.source_type} - {self.ingested_at}"


# =========================================================
# EMISSION RECORD
# =========================================================

class EmissionRecord(models.Model):

    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3

    SCOPES = [
        (1, "Scope 1"),
        (2, "Scope 2"),
        (3, "Scope 3"),
    ]

    STATUS_PENDING = "pending"
    STATUS_FLAGGED = "flagged"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUSES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_FLAGGED, "Flagged"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="records"
    )

    batch = models.ForeignKey(
        IngestionBatch,
        on_delete=models.CASCADE,
        related_name="records"
    )

    activity_date = models.DateField()

    scope = models.CharField(max_length=20)

    category = models.CharField(max_length=100)

    source_type = models.CharField(max_length=20)

    raw_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=4
    )

    raw_unit = models.CharField(max_length=50)

    normalized_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=6
    )

    normalized_unit = models.CharField(max_length=50)

    emission_factor = models.DecimalField(
        max_digits=14,
        decimal_places=8,
        null=True,
        blank=True
    )

    emission_factor_source = models.CharField(
        max_length=255,
        blank=True
    )

    co2e_kg = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True
    )

    location_code = models.CharField(
        max_length=100,
        blank=True
    )

    location_label = models.CharField(
        max_length=255,
        blank=True
    )

    vendor_or_carrier = models.CharField(
        max_length=255,
        blank=True
    )

    description = models.TextField(blank=True)

    source_row_id = models.CharField(
        max_length=255,
        blank=True
    )

    review_status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default=STATUS_PENDING
    )

    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_records"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    review_note = models.TextField(blank=True)

    is_edited = models.BooleanField(default=False)

    is_locked = models.BooleanField(default=False)

    flag_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} - {self.co2e_kg}"


# =========================================================
# AUDIT EVENT
# =========================================================

class AuditEvent(models.Model):

    ACTION_INGESTED = "ingested"
    ACTION_EDITED = "edited"
    ACTION_APPROVED = "approved"
    ACTION_REJECTED = "rejected"

    ACTIONS = [
        (ACTION_INGESTED, "Ingested"),
        (ACTION_EDITED, "Edited"),
        (ACTION_APPROVED, "Approved"),
        (ACTION_REJECTED, "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    record = models.ForeignKey(
        EmissionRecord,
        on_delete=models.CASCADE,
        related_name="audit_trail"
    )

    actor = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL
    )

    action = models.CharField(
        max_length=20,
        choices=ACTIONS
    )

    diff = models.JSONField(default=dict)

    timestamp = models.DateTimeField(auto_now_add=True)

    note = models.TextField(blank=True)


# =========================================================
# PARSE ERROR
# =========================================================

class ParseError(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    batch = models.ForeignKey(
        IngestionBatch,
        on_delete=models.CASCADE,
        related_name="parse_errors"
    )

    row_index = models.IntegerField()

    raw_content = models.TextField()

    error_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# LOCATION LOOKUP
# =========================================================

class LocationLookup(models.Model):

    tenant = models.ForeignKey(
        Tenant,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    code = models.CharField(max_length=100)

    label = models.CharField(max_length=255)

    country = models.CharField(max_length=3, blank=True)

    source_type = models.CharField(max_length=20, blank=True)