# Requirements

This file maps the Breathe ESG assignment brief to the implemented prototype and the remaining production gaps.

## Core Goal

Build and deploy a Django REST plus React prototype that can ingest enterprise ESG activity data, normalize it into a common emissions record model, and support analyst review before audit lock.

## Functional Requirements

| Requirement | Current handling |
| --- | --- |
| Ingest SAP fuel/procurement data | CSV upload through `/api/ingest/upload/` with source type `sap`. |
| Ingest utility electricity data | CSV upload through `/api/ingest/upload/` with source type `utility`. |
| Ingest corporate travel data | CSV upload through `/api/ingest/upload/` with source type `travel`. |
| Normalize activity rows | Parsers map source-specific fields into `EmissionRecord`. |
| Track failed rows | Parser failures are saved as `ParseError` rows linked to an `IngestionBatch`. |
| Flag suspicious rows | Non-positive fuel, electricity, or distance values are flagged for analyst review. |
| Review rows | Review APIs expose records, flagged records, approve, reject, batches, errors, and audit trail. |
| Lock approved rows | Approving a record sets `is_locked=True`. |
| Audit trail | Ingestion, approval, and rejection create `AuditEvent` rows. |
| Multi-tenancy | `Tenant` and `TenantMembership` exist in the data model. The prototype uses a demo tenant. |
| Deployment | Django backend is prepared for Render with PostgreSQL. React frontend is prepared for Vercel. |

## Non-Functional Requirements

| Requirement | Current handling |
| --- | --- |
| Production database | PostgreSQL is used when `DATABASE_URL` is configured. SQLite remains a local fallback. |
| Static files | WhiteNoise serves Django static files in production. |
| CORS | Frontend origins are configured by `CORS_ALLOWED_ORIGINS`. |
| Secrets | Secrets are configured through environment variables. |
| Source traceability | Each record links back to an ingestion batch and source row identifier. |
| Explainability | `MODEL.md`, `DECISIONS.md`, `TRADEOFFS.md`, and `SOURCES.md` document the design. |

## Required Deliverables

| Deliverable | File |
| --- | --- |
| Working deployed app | Live Render/Vercel URLs in submission email |
| Data model explanation | `MODEL.md` |
| Decision log | `DECISIONS.md` |
| Tradeoffs | `TRADEOFFS.md` |
| Source research | `SOURCES.md` |
| Architecture diagram | `ARCHITECTURE.md` |

## Known Gaps

- The React UI currently focuses on upload. Review functionality exists as APIs and should be surfaced in the frontend for a fuller analyst workflow.
- Source ingestion is file-upload based. Real production integrations would use SAP OData or IDoc exports, Green Button/API utility data, and SAP Concur/Navan APIs.
- Uploaded media is still local file storage. Production should use persistent object storage.
- Emission factors are simplified constants for prototype normalization.
