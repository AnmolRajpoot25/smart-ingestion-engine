# SOURCES.md

This file explains what real-world source formats were considered and how the prototype sample data was shaped.

## SAP Fuel And Procurement

### Format Researched

SAP enterprise data can be exchanged through several mechanisms:

- IDoc messages for business transactions. SAP describes an IDoc as an object that carries transaction data between systems as an electronic message: https://learning.sap.com/courses/sap-ariba-integration-features-and-functions/reviewing-immediate-document-idoc
- SAP OData services, which expose service documents and `$metadata` so clients can discover available resources and structures: https://www.sap.com/protocols/sapdata
- SAP Gateway and OData services for Fiori apps retrieving business data from back-end systems: https://help.sap.com/docs/SAP_FIORI_OVERVIEW/4694bb95aacb4cdfa1327c6d8735eaad/24d9ac6065954bf7a61f2dc9040f7870.html

### Prototype Choice

The prototype handles SAP as a flat CSV export with these fields:

- `Posting Date`
- `Plant`
- `Quantity`
- `Unit of Measure`
- `Vendor`
- `Material Description`
- `Material Number`

### Why This Sample Shape

For onboarding, a client can usually export a procurement/fuel list before API credentials are available. Plant, material, quantity, and vendor are realistic fields for fuel or procurement activity. The sample includes a negative quantity to test analyst flagging.

### What Would Break In Production

- Localized column names such as German headers.
- Mixed units such as liters, gallons, kg, and cubic meters.
- Plant codes requiring a tenant-specific lookup.
- Material descriptions that need fuel-type classification.
- SAP exports that arrive as IDoc XML or OData JSON instead of CSV.

## Utility Electricity

### Format Researched

Utility data often appears as portal exports, bills, or Green Button data. Green Button Connect My Data is an industry standard for sharing utility energy and water usage data: https://www.greenbuttonalliance.org/green-button-connect-my-data-cmd

Green Button XML represents account, bill, and usage data with schema-backed objects: https://utilityapi.com/docs/greenbutton/xml

### Prototype Choice

The prototype handles a CSV-style portal export with fields such as:

- `billing_period_start`
- `meter_id`
- `units_consumed`
- `unit`
- `utility_provider`
- `tariff_code`
- `bill_number`

### Why This Sample Shape

Facilities teams commonly work from exported utility portal reports or billing spreadsheets. The chosen fields are enough to show period, meter, consumption, provider, and bill traceability.

### What Would Break In Production

- PDF bills with values embedded in tables.
- Billing periods that cross calendar months.
- Demand charges and tariff line items.
- Interval data with 15-minute or hourly usage.
- Green Button XML that requires nested object parsing.

## Corporate Travel

### Format Researched

SAP Concur is a travel and expense platform. SAP describes Concur as helping businesses manage travel booking and expense reporting: https://help.sap.com/docs/SAP_CONCUR

SAP Concur developer docs expose expense report and entry resources through APIs, including report and entry identifiers: https://preview.developer.concur.com/api-reference/expense/expense-report/v2.expense-entry-attendee.html

SAP also provides tutorials for calling SAP Concur APIs and fetching expense reports: https://developers.sap.com/tutorials/data-to-value-conn-concur-part01..html

### Prototype Choice

The prototype handles corporate travel as a CSV export with fields such as:

- `travel_date`
- `distance_km`
- `origin`
- `destination`
- `carrier`
- `booking_ref`

### Why This Sample Shape

The goal is to normalize Scope 3 activity. Distance-based travel rows are a useful prototype because they can map directly to emissions while retaining carrier and route context.

### What Would Break In Production

- Trips with airport codes but no distance.
- Multi-leg trips.
- Hotels, rental cars, rail, and ground transport with different factors.
- Cancellations and refunds.
- SAP Concur API access limitations and customer-specific custom fields.

## Emission Factor Notes

The prototype uses simplified constants for demonstration. A production system should use a factor library with source, region, effective date, unit compatibility, and version history. Each calculated record should store enough factor metadata to explain how `co2e_kg` was produced.
