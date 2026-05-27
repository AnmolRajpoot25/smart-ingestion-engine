import csv
import io

from decimal import Decimal
from datetime import datetime


# =========================================================
# DATE PARSER
# =========================================================

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
]


def parse_date(raw):

    raw = str(raw).strip()

    for fmt in DATE_FORMATS:

        try:
            return datetime.strptime(raw, fmt).date()

        except:
            pass

    raise ValueError(f"Invalid date: {raw}")


# =========================================================
# SAFE DECIMAL
# =========================================================

def safe_decimal(value):

    cleaned = str(value).replace(",", "").strip()

    return Decimal(cleaned)


def csv_reader(text):
    sample = text[:2048]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";"

    return csv.DictReader(
        io.StringIO(text),
        dialect=dialect,
    )


# =========================================================
# SAP PARSER
# =========================================================

def parse_sap_csv(file_content):

    text = file_content.decode("utf-8-sig")

    reader = csv_reader(text)

    records = []

    for index, row in enumerate(reader):

        try:

            quantity = safe_decimal(
                row.get("Quantity", 0)
            )

            result = {

                "activity_date": parse_date(
                    row.get("Posting Date")
                ),

                "scope": "scope1",

                "category": "fuel_combustion",

                "source_type": "sap",

                "raw_quantity": quantity,

                "raw_unit": row.get(
                    "Unit of Measure",
                    "L"
                ),

                "normalized_quantity": quantity,

                "normalized_unit": row.get(
                    "Unit of Measure",
                    "L"
                ),

                "co2e_kg": quantity * Decimal("2.68"),

                "location_code": row.get(
                    "Plant",
                    ""
                ),

                "vendor_or_carrier": row.get(
                    "Vendor",
                    ""
                ),

                "description": row.get(
                    "Material Description",
                    ""
                ),

                "source_row_id": row.get(
                    "Material Number",
                    ""
                ),

                "flag_reason": "",
            }

            # -----------------------------------------
            # FLAG NEGATIVE VALUES
            # -----------------------------------------

            if quantity <= 0:

                result["flag_reason"] = (
                    "Non-positive quantity"
                )

            records.append(result)

        except Exception as exc:

            records.append({

                "_error": str(exc),

                "_row_index": index,

                "_raw": str(row),
            })

    return records


# =========================================================
# UTILITY PARSER
# =========================================================

def parse_utility_csv(file_content):

    text = file_content.decode("utf-8-sig")

    reader = csv_reader(text)

    records = []

    for index, row in enumerate(reader):

        try:

            quantity = safe_decimal(
                row.get("units_consumed", 0)
            )

            result = {

                "activity_date": parse_date(
                    row.get("billing_period_start")
                ),

                "scope": "scope2",

                "category": "electricity",

                "source_type": "utility",

                "raw_quantity": quantity,

                "raw_unit": row.get(
                    "unit",
                    "kWh"
                ),

                "normalized_quantity": quantity,

                "normalized_unit": row.get(
                    "unit",
                    "kWh"
                ),

                "co2e_kg": quantity * Decimal("0.708"),

                "location_code": row.get(
                    "meter_id",
                    ""
                ),

                "vendor_or_carrier": row.get(
                    "utility_provider",
                    ""
                ),

                "description": row.get(
                    "tariff_code",
                    ""
                ),

                "source_row_id": row.get(
                    "bill_number",
                    ""
                ),

                "flag_reason": "",
            }

            if quantity <= 0:

                result["flag_reason"] = (
                    "Invalid electricity consumption"
                )

            records.append(result)

        except Exception as exc:

            records.append({

                "_error": str(exc),

                "_row_index": index,

                "_raw": str(row),
            })

    return records


# =========================================================
# TRAVEL PARSER
# =========================================================

def parse_travel_csv(file_content):

    text = file_content.decode("utf-8-sig")

    reader = csv_reader(text)

    records = []

    for index, row in enumerate(reader):

        try:

            distance = safe_decimal(
                row.get("distance_km", 0)
            )

            result = {

                "activity_date": parse_date(
                    row.get("travel_date")
                ),

                "scope": "scope3",

                "category": "flight",

                "source_type": "travel",

                "raw_quantity": distance,

                "raw_unit": "km",

                "normalized_quantity": distance,

                "normalized_unit": "km",

                "co2e_kg": distance * Decimal("0.155"),

                "location_code": row.get(
                    "origin",
                    ""
                ),

                "vendor_or_carrier": row.get(
                    "carrier",
                    ""
                ),

                "description": (
                    f"{row.get('origin')} → "
                    f"{row.get('destination')}"
                ),

                "source_row_id": row.get(
                    "booking_ref",
                    ""
                ),

                "flag_reason": "",
            }

            if distance <= 0:

                result["flag_reason"] = (
                    "Invalid travel distance"
                )

            records.append(result)

        except Exception as exc:

            records.append({

                "_error": str(exc),

                "_row_index": index,

                "_raw": str(row),
            })

    return records
