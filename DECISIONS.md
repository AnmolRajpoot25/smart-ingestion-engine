# DECISIONS.md

## 1. File Upload First, API Pull Later

Decision: use file upload for SAP, utility, and travel sources in the prototype.

Why:

- The assignment allows choosing the ingestion mechanism.
- Enterprise API access usually requires credentials, security review, tenant configuration, and vendor-specific setup.
- A 4-day prototype can show the harder data-modeling and normalization work through realistic exports.

What I would ask the PM:

- Do we already have API credentials for SAP, utility providers, or Concur/Navan?
- Is the first onboarding expected to be historical backfill or ongoing scheduled ingestion?
- Are analysts allowed to upload files manually, or must all data arrive through managed integrations?

## 2. SAP Subset

Decision: handle SAP fuel/procurement as a flat export with fields such as posting date, plant, quantity, unit, vendor, material description, and material number.

Why:

- SAP can expose data through IDocs, OData, BAPIs, or plain exports.
- For onboarding, a client can usually produce an export faster than granting API access.
- The parser focuses on fuel-like procurement rows that can map into Scope 1 activity.

Ignored for now:

- German/localized column headers.
- Material master lookups.
- Plant lookup enrichment.
- Mixed units requiring conversion.
- Direct SAP OData authentication.

## 3. Utility Subset

Decision: handle utility electricity as portal-style CSV exports.

Why:

- Facilities teams often download bills or usage reports from utility portals.
- CSV is easier to prototype than PDF bill extraction.
- The model still leaves room for billing periods, meter IDs, units, and provider names.

Ignored for now:

- PDF bill parsing.
- Green Button XML import.
- Interval meter data.
- Tariff-line item allocation.
- Calendar-month apportionment.

## 4. Travel Subset

Decision: handle travel as corporate travel export rows with travel date, distance, carrier/vendor, origin, destination, and booking reference.

Why:

- Travel platforms expose expense entries, itineraries, and reports, but API access varies by customer setup.
- CSV export is enough to show Scope 3 normalization and review.
- Distance-based emissions are a defensible prototype simplification.

Ignored for now:

- Airport-code distance calculation.
- Hotel-night factors.
- Rental car fuel type.
- Rail and ground transport categories.
- SAP Concur OAuth and report-entry API integration.

## 5. One Normalized EmissionRecord Table

Decision: store all normalized source rows in `EmissionRecord`.

Why:

- Analysts need one review queue, not separate tables per source.
- Scope, category, source type, and raw metadata preserve differences between sources.
- This makes approval, rejection, locking, and audit events consistent.

Tradeoff:

- Highly source-specific fields are not modeled as first-class columns yet.

## 6. Preserve Raw Values

Decision: keep `raw_quantity` and `raw_unit` beside normalized values.

Why:

- Auditors need to trace calculations back to the source.
- Analysts need to see whether a suspicious number came from the file or from normalization.

## 7. Flag Suspicious Rows Instead Of Rejecting Them

Decision: non-positive quantities become flagged records where possible.

Why:

- Enterprise data often contains reversals, credits, corrections, or negative adjustments.
- Automatically deleting or rejecting such rows would hide important accounting context.

## 8. PostgreSQL For Deployment

Decision: use PostgreSQL in production through `DATABASE_URL`, with SQLite as a local fallback.

Why:

- Render provides managed PostgreSQL.
- Django runs cleanly against both local SQLite and production PostgreSQL.
- PostgreSQL is more appropriate for deployed multi-user review workflows.

## 9. Environment Variables For Deployment

Decision: use environment variables for secret key, debug mode, hosts, CORS, CSRF, and database URL.

Why:

- Secrets should not live in source code.
- Render and Vercel are environment-driven.
- The same code can run locally and in production.
