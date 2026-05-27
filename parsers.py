import csv
import io
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation


# ─────────────────────────────────────────────
# UNIT NORMALISATION HELPERS
# All quantities are normalized before storage.
# SAP delivers litres, gallons, m3, kg depending on plant locale.
# Utility bills mix kWh, MWh, therms.
# Travel platforms mix km, miles, sometimes nothing at all.
# ─────────────────────────────────────────────

UNIT_CONVERSIONS = {
    # volume → litres
    "L": Decimal("1"),
    "LITER": Decimal("1"),
    "LITRE": Decimal("1"),
    "GAL": Decimal("3.78541"),
    "GALLON": Decimal("3.78541"),
    "M3": Decimal("1000"),
    "CBM": Decimal("1000"),
    # mass → kg
    "KG": Decimal("1"),
    "KILOGRAM": Decimal("1"),
    "T": Decimal("1000"),
    "TONNE": Decimal("1000"),
    "MT": Decimal("1000"),
    "LB": Decimal("0.453592"),
    "POUND": Decimal("0.453592"),
    # energy → kWh
    "KWH": Decimal("1"),
    "MWH": Decimal("1000"),
    "GWH": Decimal("1000000"),
    "THERM": Decimal("29.3001"),
    "MMBTU": Decimal("293.071"),
    # distance → km
    "KM": Decimal("1"),
    "KILOMETRE": Decimal("1"),
    "KILOMETER": Decimal("1"),
    "MI": Decimal("1.60934"),
    "MILE": Decimal("1.60934"),
    "NM": Decimal("1.852"),
    "NAUTICALMILE": Decimal("1.852"),
}

UNIT_BASE = {
    "L": "litres", "LITER": "litres", "LITRE": "litres",
    "GAL": "litres", "GALLON": "litres", "M3": "litres", "CBM": "litres",
    "KG": "kg", "KILOGRAM": "kg", "T": "kg", "TONNE": "kg",
    "MT": "kg", "LB": "kg", "POUND": "kg",
    "KWH": "kWh", "MWH": "kWh", "GWH": "kWh",
    "THERM": "kWh", "MMBTU": "kWh",
    "KM": "km", "KILOMETRE": "km", "KILOMETER": "km",
    "MI": "km", "MILE": "km", "NM": "km", "NAUTICALMILE": "km",
}


def normalize_unit(quantity: Decimal, unit: str) -> tuple[Decimal, str]:
    key = re.sub(r"[\s\-_]", "", unit).upper()
    factor = UNIT_CONVERSIONS.get(key)
    if factor is None:
        return quantity, unit  # return as-is; flag row downstream
    return (quantity * factor).quantize(Decimal("0.000001")), UNIT_BASE[key]


# ─────────────────────────────────────────────
# DATE PARSING
# SAP dates arrive as DD.MM.YYYY (German locale), YYYYMMDD (IDoc),
# MM/DD/YYYY (US config), or ISO 8601. We try them all in order.
# ─────────────────────────────────────────────

DATE_FORMATS = [
    "%d.%m.%Y",   # SAP German locale: 15.03.2024
    "%Y%m%d",     # SAP IDoc compact: 20240315
    "%m/%d/%Y",   # US format: 03/15/2024
    "%Y-%m-%d",   # ISO 8601: 2024-03-15
    "%d/%m/%Y",   # EU slash: 15/03/2024
    "%d-%m-%Y",   # EU dash: 15-03-2024
    "%b %d, %Y",  # Navan: Mar 15, 2024
    "%B %d, %Y",  # Navan long: March 15, 2024
]


def parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {raw!r}")


def safe_decimal(raw: str) -> Decimal:
    cleaned = re.sub(r"[^\d.\-]", "", raw.strip().replace(",", "."))
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"Cannot parse number: {raw!r}")


# ─────────────────────────────────────────────
# EMISSION FACTORS
# DEFRA 2023 / EPA factors, stored inline for now.
# In production these would live in a versioned DB table.
# Factors are in kgCO2e per unit.
# ─────────────────────────────────────────────

EMISSION_FACTORS = {
    # fuel: kgCO2e per litre
    "diesel": {"factor": Decimal("2.6820"), "source": "DEFRA 2023"},
    "petrol": {"factor": Decimal("2.3120"), "source": "DEFRA 2023"},
    "natural_gas": {"factor": Decimal("2.0426"), "source": "DEFRA 2023"},  # per m3
    "lpg": {"factor": Decimal("1.5551"), "source": "DEFRA 2023"},
    # electricity: kgCO2e per kWh (India grid average 2023)
    "electricity_india": {"factor": Decimal("0.7080"), "source": "CEA India 2023"},
    "electricity_uk": {"factor": Decimal("0.2156"), "source": "DEFRA 2023"},
    "electricity_us": {"factor": Decimal("0.3860"), "source": "EPA 2023"},
    "electricity_generic": {"factor": Decimal("0.4330"), "source": "IEA World Average 2022"},
    # flight: kgCO2e per km per passenger (includes RFI factor 1.9)
    "flight_economy": {"factor": Decimal("0.1550"), "source": "DEFRA 2023 + RFI"},
    "flight_business": {"factor": Decimal("0.4290"), "source": "DEFRA 2023 + RFI"},
    "flight_first": {"factor": Decimal("0.5870"), "source": "DEFRA 2023 + RFI"},
    # hotel: kgCO2e per room-night
    "hotel_night": {"factor": Decimal("31.0000"), "source": "Cornell Hotel Sustainability Benchmarking 2022"},
    # ground: kgCO2e per km
    "taxi": {"factor": Decimal("0.1489"), "source": "DEFRA 2023"},
    "car_rental": {"factor": Decimal("0.1680"), "source": "DEFRA 2023"},
    "rail": {"factor": Decimal("0.0369"), "source": "DEFRA 2023"},
}


def get_emission_factor(category: str, sub_type: str = "") -> tuple[Decimal, str]:
    key = f"{category}_{sub_type}" if sub_type else category
    ef = EMISSION_FACTORS.get(key) or EMISSION_FACTORS.get(category)
    if ef:
        return ef["factor"], ef["source"]
    return None, ""


# ─────────────────────────────────────────────
# AIRPORT DISTANCE TABLE (IATA pair → km)
# Real deployment would call a GCD API.
# This covers the most common Indian corporate travel corridors.
# ─────────────────────────────────────────────

AIRPORT_DISTANCES = {
    frozenset(["DEL", "BOM"]): 1148,
    frozenset(["DEL", "BLR"]): 1740,
    frozenset(["DEL", "HYD"]): 1253,
    frozenset(["DEL", "MAA"]): 1756,
    frozenset(["BOM", "BLR"]): 842,
    frozenset(["BOM", "HYD"]): 711,
    frozenset(["BOM", "CCU"]): 1660,
    frozenset(["DEL", "LHR"]): 6710,
    frozenset(["BOM", "LHR"]): 7188,
    frozenset(["DEL", "JFK"]): 11763,
    frozenset(["DEL", "SIN"]): 4148,
    frozenset(["BOM", "DXB"]): 1927,
}


def airport_distance_km(origin: str, destination: str) -> int:
    key = frozenset([origin.upper(), destination.upper()])
    dist = AIRPORT_DISTANCES.get(key)
    if dist is None:
        # Great-circle fallback using a hardcoded very rough estimate
        # Real deployment: call aviation edge or OpenFlights API
        raise ValueError(f"No distance data for {origin}-{destination}. Add to AIRPORT_DISTANCES or wire API.")
    return dist


# ─────────────────────────────────────────────
# SAP FLAT-FILE PARSER
# Chosen format: SAP ECC flat-file export (transaction MB52/ME2M style).
# Justification: IDoc is binary/XML and requires ALE middleware.
# OData requires S/4HANA. Flat-file is the lowest-common-denominator
# that works on any SAP version via SE16/SM30 exports.
# Headers may be German; we map them explicitly.
# ─────────────────────────────────────────────

SAP_COLUMN_MAP = {
    # German → canonical
    "Buchungsdatum": "posting_date",
    "Belegdatum": "document_date",
    "Werk": "plant_code",
    "Materialnummer": "material_number",
    "Materialbezeichnung": "material_description",
    "Menge": "quantity",
    "Mengeneinheit": "unit",
    "Bewegungsart": "movement_type",
    "Lieferant": "vendor",
    "Buchungsbetrag": "amount",
    # English (some SAP configs export English)
    "Posting Date": "posting_date",
    "Document Date": "document_date",
    "Plant": "plant_code",
    "Material Number": "material_number",
    "Material Description": "material_description",
    "Quantity": "quantity",
    "Unit of Measure": "unit",
    "Movement Type": "movement_type",
    "Vendor": "vendor",
    "Amount": "amount",
}

FUEL_KEYWORDS = [
    "diesel", "petrol", "benzin", "kraftstoff", "fuel", "gasoline",
    "lpg", "natural gas", "erdgas", "heating oil",
]

MOVEMENT_TYPES_GOODS_ISSUE = {"201", "261", "551", "601"}  # consumption / goods issue


def classify_sap_material(description: str, material_no: str) -> tuple[str, str]:
    """Return (category, fuel_type) for a SAP material row."""
    desc_lower = description.lower()
    for kw in FUEL_KEYWORDS:
        if kw in desc_lower:
            fuel_type = "diesel" if "diesel" in desc_lower else (
                "petrol" if any(x in desc_lower for x in ["petrol", "benzin", "gasoline"]) else (
                    "natural_gas" if any(x in desc_lower for x in ["gas", "erdgas"]) else "lpg"
                )
            )
            return "fuel_combustion", fuel_type
    return "procurement", ""


def parse_sap_csv(file_content: bytes) -> list[dict]:
    """
    Parse a SAP flat-file CSV export.
    Returns a list of dicts ready to be mapped to EmissionRecord fields.
    Raises on total failure; partial row failures are returned as error dicts.
    """
    text = file_content.decode("utf-8-sig", errors="replace")  # strip BOM, tolerate latin-1 chars
    reader = csv.DictReader(io.StringIO(text), delimiter=";")   # SAP uses semicolons

    if not reader.fieldnames:
        raise ValueError("SAP file has no headers")

    # Remap headers from German/English to canonical names
    canonical_headers = {col: SAP_COLUMN_MAP.get(col, col) for col in reader.fieldnames}
    records = []

    for i, row in enumerate(reader):
        remapped = {canonical_headers.get(k, k): v for k, v in row.items()}
        result = {"_row_index": i, "_raw": str(row), "_source": "sap"}

        try:
            # Skip non-consumption movement types if movement_type column present
            mt = remapped.get("movement_type", "").strip()
            if mt and mt not in MOVEMENT_TYPES_GOODS_ISSUE:
                continue

            raw_date = remapped.get("posting_date") or remapped.get("document_date", "")
            result["activity_date"] = parse_date(raw_date)

            raw_qty = remapped.get("quantity", "0")
            result["raw_quantity"] = safe_decimal(raw_qty)
            result["raw_unit"] = remapped.get("unit", "L").strip()

            norm_qty, norm_unit = normalize_unit(result["raw_quantity"], result["raw_unit"])
            result["normalized_quantity"] = norm_qty
            result["normalized_unit"] = norm_unit

            desc = remapped.get("material_description", "")
            mat_no = remapped.get("material_number", "")
            category, fuel_type = classify_sap_material(desc, mat_no)
            result["category"] = category
            result["scope"] = 1 if category == "fuel_combustion" else 3
            result["location_code"] = remapped.get("plant_code", "").strip()
            result["vendor_or_carrier"] = remapped.get("vendor", "").strip()
            result["description"] = desc
            result["source_row_id"] = mat_no or str(i)

            # Compute CO2e
            factor, factor_source = get_emission_factor(fuel_type or category)
            if factor:
                result["emission_factor"] = factor
                result["emission_factor_source"] = factor_source
                result["co2e_kg"] = (norm_qty * factor).quantize(Decimal("0.0001"))

            # Flag suspicious rows
            flags = []
            if result["raw_quantity"] <= 0:
                flags.append("non-positive quantity")
            if not result["location_code"]:
                flags.append("missing plant code")
            if not factor:
                flags.append(f"no emission factor for material: {desc[:60]}")
            result["flag_reason"] = "; ".join(flags)

        except Exception as exc:
            result["_error"] = str(exc)

        records.append(result)

    return records


# ─────────────────────────────────────────────
# UTILITY CSV PARSER
# Chosen format: CSV export from utility portal (Tata Power / MSEDCL style).
# Justification: PDFs require OCR which is fragile and slow.
# APIs exist only for large utilities with AMI meters.
# Portal CSV export is the most common real-world workflow for Indian enterprises.
# Fields: meter_id, billing_period_start, billing_period_end, units_consumed, unit, tariff_code
# ─────────────────────────────────────────────

def parse_utility_csv(file_content: bytes) -> list[dict]:
    text = file_content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("Utility file has no headers")

    # Normalise header names (strip spaces, lowercase)
    norm_headers = {h: h.strip().lower().replace(" ", "_") for h in reader.fieldnames}
    records = []

    for i, row in enumerate(reader):
        remapped = {norm_headers.get(k, k.lower()): v for k, v in row.items()}
        result = {"_row_index": i, "_raw": str(row), "_source": "utility"}

        try:
            # Billing period: utility bills don't align to calendar months
            # We capture both start and end, use midpoint as activity_date
            period_start = parse_date(remapped.get("billing_period_start") or remapped.get("period_start", ""))
            period_end = parse_date(remapped.get("billing_period_end") or remapped.get("period_end", ""))
            mid = date.fromordinal((period_start.toordinal() + period_end.toordinal()) // 2)
            result["activity_date"] = mid
            result["period_start"] = period_start
            result["period_end"] = period_end

            raw_qty = remapped.get("units_consumed") or remapped.get("consumption") or remapped.get("quantity", "0")
            result["raw_quantity"] = safe_decimal(raw_qty)
            result["raw_unit"] = remapped.get("unit", "kWh").strip()

            norm_qty, norm_unit = normalize_unit(result["raw_quantity"], result["raw_unit"])
            result["normalized_quantity"] = norm_qty
            result["normalized_unit"] = norm_unit

            result["category"] = "electricity"
            result["scope"] = 2
            result["location_code"] = remapped.get("meter_id", "").strip()
            result["description"] = remapped.get("tariff_code", "") or remapped.get("description", "")
            result["vendor_or_carrier"] = remapped.get("utility_provider", "").strip()
            result["source_row_id"] = remapped.get("bill_number", str(i)).strip()

            # India grid factor by default; override if country column present
            country = remapped.get("country", "IN").strip().upper()
            ef_key = {"IN": "electricity_india", "GB": "electricity_uk", "US": "electricity_us"}.get(
                country, "electricity_generic"
            )
            factor, factor_source = get_emission_factor(ef_key)
            if factor:
                result["emission_factor"] = factor
                result["emission_factor_source"] = factor_source
                result["co2e_kg"] = (norm_qty * factor).quantize(Decimal("0.0001"))

            flags = []
            if result["raw_quantity"] <= 0:
                flags.append("non-positive consumption")
            if (period_end - period_start).days > 95:
                flags.append("billing period > 95 days — possible duplicate")
            result["flag_reason"] = "; ".join(flags)

        except Exception as exc:
            result["_error"] = str(exc)

        records.append(result)

    return records


# ─────────────────────────────────────────────
# TRAVEL CSV PARSER
# Chosen format: Navan / TripActions expense export CSV.
# Justification: Navan is the dominant platform in Indian tech enterprises.
# Their export includes trip_type, origin, destination (airport codes for flights),
# cabin_class, nights (for hotels), distance_km (for ground, when available).
# ─────────────────────────────────────────────

TRAVEL_TYPE_MAP = {
    "air": "flight", "flight": "flight", "fly": "flight",
    "hotel": "hotel", "accommodation": "hotel",
    "cab": "ground_transport", "taxi": "ground_transport",
    "car": "ground_transport", "uber": "ground_transport",
    "train": "ground_transport", "rail": "ground_transport", "metro": "ground_transport",
}

CABIN_MAP = {
    "economy": "flight_economy", "eco": "flight_economy", "y": "flight_economy",
    "business": "flight_business", "biz": "flight_business", "c": "flight_business",
    "first": "flight_first", "f": "flight_first",
}


def parse_travel_csv(file_content: bytes) -> list[dict]:
    text = file_content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("Travel file has no headers")

    norm_headers = {h: h.strip().lower().replace(" ", "_") for h in reader.fieldnames}
    records = []

    for i, row in enumerate(reader):
        remapped = {norm_headers.get(k, k.lower()): v for k, v in row.items()}
        result = {"_row_index": i, "_raw": str(row), "_source": "travel"}

        try:
            raw_date = remapped.get("travel_date") or remapped.get("departure_date") or remapped.get("date", "")
            result["activity_date"] = parse_date(raw_date)
            result["scope"] = 3

            trip_type_raw = remapped.get("trip_type") or remapped.get("type") or remapped.get("category", "")
            trip_type = TRAVEL_TYPE_MAP.get(trip_type_raw.lower().strip(), "ground_transport")
            result["category"] = trip_type

            origin = remapped.get("origin") or remapped.get("from", "")
            destination = remapped.get("destination") or remapped.get("to", "")
            result["description"] = f"{origin.upper()} → {destination.upper()}"
            result["location_code"] = origin.upper()[:3]
            result["vendor_or_carrier"] = remapped.get("carrier") or remapped.get("airline") or remapped.get("vendor", "")
            result["source_row_id"] = remapped.get("booking_ref") or remapped.get("transaction_id", str(i))

            if trip_type == "flight":
                # Distance: use column if provided, else look up airport pair
                raw_dist = remapped.get("distance_km", "").strip()
                if raw_dist:
                    distance_km = safe_decimal(raw_dist)
                else:
                    distance_km = Decimal(airport_distance_km(origin.strip()[:3], destination.strip()[:3]))

                result["raw_quantity"] = distance_km
                result["raw_unit"] = "km"
                result["normalized_quantity"] = distance_km
                result["normalized_unit"] = "km"

                cabin_raw = remapped.get("cabin_class", "economy").lower().strip()
                ef_key = CABIN_MAP.get(cabin_raw, "flight_economy")
                factor, factor_source = get_emission_factor(ef_key)

            elif trip_type == "hotel":
                nights = safe_decimal(remapped.get("nights", "1"))
                result["raw_quantity"] = nights
                result["raw_unit"] = "nights"
                result["normalized_quantity"] = nights
                result["normalized_unit"] = "nights"
                factor, factor_source = get_emission_factor("hotel_night")

            else:
                # Ground transport
                raw_dist = remapped.get("distance_km", "0").strip() or "0"
                distance_km = safe_decimal(raw_dist)
                result["raw_quantity"] = distance_km
                result["raw_unit"] = "km"
                result["normalized_quantity"] = distance_km
                result["normalized_unit"] = "km"
                transport_type = remapped.get("transport_mode", "taxi").lower()
                ef_key = {"train": "rail", "rail": "rail"}.get(transport_type, "taxi")
                factor, factor_source = get_emission_factor(ef_key)

            if factor:
                result["emission_factor"] = factor
                result["emission_factor_source"] = factor_source
                result["co2e_kg"] = (result["normalized_quantity"] * factor).quantize(Decimal("0.0001"))

            flags = []
            if result.get("normalized_quantity", 0) <= 0:
                flags.append("zero or missing distance/quantity")
            if trip_type == "flight" and not origin and not destination:
                flags.append("missing origin/destination")
            result["flag_reason"] = "; ".join(flags)

        except Exception as exc:
            result["_error"] = str(exc)

        records.append(result)

    return records