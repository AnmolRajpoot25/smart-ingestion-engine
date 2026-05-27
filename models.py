import uuid
from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────
# TENANT LAYER
# Every object is scoped to a Tenant.
# Analysts belong to a Tenant; data never leaks across tenants.
# ─────────────────────────────────────────────

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
    ROLES = [(ROLE_ANALYST, "Analyst"), (ROLE_ADMIN, "Admin")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=20, choices=ROLES, default=ROLE_ANALYST)

    class Meta:
        unique_together = ("user", "tenant")


# ─────────────────────────────────────────────
# INGESTION BATCH
# One IngestionBatch = one upload or pull event.
# Tracks source type, raw payload reference, and ingestion metadata.
# The batch is immutable once closed; rows point back to it.
# ─────────────────────────────────────────────

class IngestionBatch(models.Model):
    SOURCE_SAP = "sap"
    SOURCE_UTILITY = "utility"
    SOURCE_TRAVEL = "travel"
    SOURCES = [
        (SOURCE_SAP, "SAP Fuel & Procurement"),
        (SOURCE_UTILITY, "Utility Electricity"),
        (SOURCE_TRAVEL, "Corporate Travel"),
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
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="batches")
    source_type = models.CharField(max_length=20, choices=SOURCES)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    raw_file = models.FileField(upload_to="raw/%Y/%m/", null=True, blank=True)
    raw_file_name = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    ingested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-ingested_at"]

    def __str__(self):
        return f"{self.tenant.slug} / {self.source_type} / {self.ingested_at:%Y-%m-%d}"


# ─────────────────────────────────────────────
# CANONICAL EMISSION RECORD
# One row = one normalized activity entry.
# All three sources produce EmissionRecord rows.
# Scope classification follows GHG Protocol:
#   Scope 1 = direct (fuel combustion, fleet)
#   Scope 2 = indirect electricity
#   Scope 3 = value chain (travel, procurement)
# ─────────────────────────────────────────────

class EmissionRecord(models.Model):
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3
    SCOPES = [(1, "Scope 1"), (2, "Scope 2"), (3, "Scope 3")]

    CATEGORY_FUEL = "fuel_combustion"
    CATEGORY_ELECTRICITY = "electricity"
    CATEGORY_FLIGHT = "flight"
    CATEGORY_HOTEL = "hotel"
    CATEGORY_GROUND = "ground_transport"
    CATEGORY_PROCUREMENT = "procurement"
    CATEGORIES = [
        (CATEGORY_FUEL, "Fuel Combustion"),
        (CATEGORY_ELECTRICITY, "Purchased Electricity"),
        (CATEGORY_FLIGHT, "Business Flight"),
        (CATEGORY_HOTEL, "Hotel Stay"),
        (CATEGORY_GROUND, "Ground Transport"),
        (CATEGORY_PROCUREMENT, "Procurement"),
    ]

    STATUS_PENDING = "pending"
    STATUS_FLAGGED = "flagged"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUSES = [
        (STATUS_PENDING, "Pending Review"),
        (STATUS_FLAGGED, "Flagged"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="records")
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="records")

    # ── Activity window ──────────────────────────────────────────────────
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    # ── Classification ───────────────────────────────────────────────────
    scope = models.IntegerField(choices=SCOPES)
    category = models.CharField(max_length=40, choices=CATEGORIES)
    source_type = models.CharField(max_length=20)

    # ── Raw activity quantity ─────────────────────────────────────────────
    raw_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    raw_unit = models.CharField(max_length=50)
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=6)
    normalized_unit = models.CharField(max_length=50)

    # ── Emission computation ──────────────────────────────────────────────
    emission_factor = models.DecimalField(max_digits=14, decimal_places=8, null=True, blank=True)
    emission_factor_source = models.CharField(max_length=255, blank=True)
    co2e_kg = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    # ── Source metadata ──────────────────────────────────────────────────
    location_code = models.CharField(max_length=100, blank=True)
    location_label = models.CharField(max_length=255, blank=True)
    vendor_or_carrier = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    source_row_id = models.CharField(max_length=255, blank=True)

    # ── Review workflow ───────────────────────────────────────────────────
    review_status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_records"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)

    # ── Audit flags ──────────────────────────────────────────────────────
    is_edited = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    flag_reason = models.TextField(blank=True)

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-activity_date"]
        indexes = [
            models.Index(fields=["tenant", "review_status"]),
            models.Index(fields=["tenant", "scope"]),
            models.Index(fields=["batch"]),
        ]

    def __str__(self):
        return f"{self.category} / {self.activity_date} / {self.co2e_kg} kgCO2e"


# ─────────────────────────────────────────────
# AUDIT TRAIL
# Immutable log. Every state change appends a row here.
# Never deleted. This is what auditors actually see.
# ─────────────────────────────────────────────

class AuditEvent(models.Model):
    ACTION_INGESTED = "ingested"
    ACTION_EDITED = "edited"
    ACTION_APPROVED = "approved"
    ACTION_REJECTED = "rejected"
    ACTION_FLAGGED = "flagged"
    ACTION_LOCKED = "locked"
    ACTIONS = [
        (ACTION_INGESTED, "Ingested"),
        (ACTION_EDITED, "Edited"),
        (ACTION_APPROVED, "Approved"),
        (ACTION_REJECTED, "Rejected"),
        (ACTION_FLAGGED, "Auto-flagged"),
        (ACTION_LOCKED, "Locked for audit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name="audit_trail")
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=ACTIONS)
    diff = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["timestamp"]


# ─────────────────────────────────────────────
# PARSE ERROR LOG
# Rows that fail parsing never silently disappear.
# Each failure gets a ParseError with the raw line and reason.
# ─────────────────────────────────────────────

class ParseError(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="parse_errors")
    row_index = models.IntegerField()
    raw_content = models.TextField()
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_index"]


# ─────────────────────────────────────────────
# LOOKUP TABLES
# SAP plant codes, meter IDs, airport IATA codes → human labels.
# Tenants can override global lookups with their own mappings.
# ─────────────────────────────────────────────

class LocationLookup(models.Model):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE)
    code = models.CharField(max_length=100)
    label = models.CharField(max_length=255)
    country = models.CharField(max_length=3, blank=True)
    source_type = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ("tenant", "code", "source_type")