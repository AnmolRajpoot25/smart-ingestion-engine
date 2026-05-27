from django.contrib import admin

from .models import (
    Tenant,
    TenantMembership,
    IngestionBatch,
    EmissionRecord,
    AuditEvent,
    ParseError,
    LocationLookup,
)

admin.site.register(Tenant)
admin.site.register(TenantMembership)
admin.site.register(IngestionBatch)
admin.site.register(EmissionRecord)
admin.site.register(AuditEvent)
admin.site.register(ParseError)
admin.site.register(LocationLookup)