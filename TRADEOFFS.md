# TRADEOFFS.md

## 1. No Full Analyst Dashboard Yet

What was not built:

A complete React review dashboard with filtering, batch drilldown, parse-error review, row approval, row rejection, and audit trail display.

Why:

The backend review APIs exist, but the prototype time was focused on ingestion, normalization, deployment, and data model traceability. A polished dashboard would be the next highest-value product step.

What I would build next:

- Batch summary screen.
- Records table with pending, flagged, approved, rejected tabs.
- Parse error table grouped by batch.
- Approve and reject actions.
- Audit trail drawer per record.

## 2. No Real Vendor API Integrations

What was not built:

Direct SAP, utility, Concur, or Navan API integrations.

Why:

Those integrations require credentials, customer-specific configuration, auth flows, and production security decisions. For a 4-day prototype, realistic CSV ingestion shows the modeling and normalization approach without pretending API access is trivial.

What I would build next:

- SAP OData connector for a selected entity set.
- Green Button XML parser or utility API connector.
- SAP Concur expense/travel export connector.
- Scheduled ingestion jobs with source health monitoring.

## 3. Simplified Emission Factor Logic

What was not built:

A production-grade factor engine with region, fuel type, date, supplier, method, and factor-source versioning.

Why:

The assignment is primarily about ingestion shape, normalization, and review. Hardcoding simple factors is acceptable for a prototype only if documented clearly.

What I would build next:

- `EmissionFactor` table.
- Factor source/version fields on each calculation.
- Country and grid-region mapping.
- Calculation explanation per row.
- Recalculation workflow when factors change.

## 4. Local Media Storage

What was not built:

Persistent cloud storage for uploaded source files.

Why:

The prototype stores uploaded files through Django file storage. On many hosts, local files are not durable across deploys or instance replacement.

What I would build next:

- S3-compatible object storage.
- Raw-file checksum.
- Virus scan hook for uploads.
- Retention policy by tenant.

## 5. Minimal Auth

What was not built:

Tenant-aware login, role permissions, and user management.

Why:

The data model supports tenants and memberships, but the prototype uses demo users to keep ingestion and review flows simple.

What I would build next:

- Login and logout.
- Tenant-scoped querysets.
- Analyst/admin/auditor roles.
- Object-level permission checks.
