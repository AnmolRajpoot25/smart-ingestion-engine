from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import render

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import (
    Tenant,
    IngestionBatch,
    EmissionRecord,
    ParseError,
    AuditEvent,
)

from .parsers import (
    parse_sap_csv,
    parse_utility_csv,
    parse_travel_csv,
)


# =========================================================
# INGESTION API
# =========================================================

class UploadIngestionAPIView(APIView):

    parser_classes = [MultiPartParser, FormParser]

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    def get(self, request):
        return render(request, "upload.html")

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    def post(self, request):

        source_type = request.data.get("source_type")
        uploaded_file = request.FILES.get("file")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not source_type:
            return Response(
                {"error": "source_type is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not uploaded_file:
            return Response(
                {"error": "file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------------------------------
        # TEMP USER + TENANT
        # -------------------------------------------------

        tenant, _ = Tenant.objects.get_or_create(
            slug="demo-company",
            defaults={"name": "Demo Company"}
        )

        user, _ = User.objects.get_or_create(
            username="system_user"
        )

        # -------------------------------------------------
        # CREATE INGESTION BATCH
        # -------------------------------------------------

        batch = IngestionBatch.objects.create(
            tenant=tenant,
            source_type=source_type,
            uploaded_by=user,
            raw_file=uploaded_file,
            raw_file_name=uploaded_file.name,
            status=IngestionBatch.STATUS_PROCESSING,
        )

        try:

            # -------------------------------------------------
            # READ FILE CONTENT
            # -------------------------------------------------

            uploaded_file.seek(0)

            file_content = uploaded_file.read()

            # -------------------------------------------------
            # PARSE FILE
            # -------------------------------------------------

            if source_type == "sap":

                parsed_rows = parse_sap_csv(file_content)

            elif source_type == "utility":

                parsed_rows = parse_utility_csv(file_content)

            elif source_type == "travel":

                parsed_rows = parse_travel_csv(file_content)

            else:

                return Response(
                    {"error": "Invalid source_type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # -------------------------------------------------
            # DEBUG OUTPUT
            # -------------------------------------------------

            print("====================================")
            print("PARSED ROWS:")
            print(parsed_rows)
            print("TOTAL ROWS:", len(parsed_rows))
            print("====================================")

            success_count = 0
            error_count = 0

            # -------------------------------------------------
            # PROCESS EACH ROW
            # -------------------------------------------------

            for row in parsed_rows:

                # ---------------------------------------------
                # PARSE ERROR ROW
                # ---------------------------------------------

                if "_error" in row:

                    ParseError.objects.create(
                        batch=batch,
                        row_index=row.get("_row_index", 0),
                        raw_content=row.get("_raw", ""),
                        error_message=row["_error"],
                    )

                    error_count += 1
                    continue

                # ---------------------------------------------
                # REVIEW STATUS
                # ---------------------------------------------

                review_status = (
                    EmissionRecord.STATUS_FLAGGED
                    if row.get("flag_reason")
                    else EmissionRecord.STATUS_PENDING
                )

                # ---------------------------------------------
                # CREATE RECORD
                # ---------------------------------------------

                try:

                    record = EmissionRecord.objects.create(

                        tenant=tenant,
                        batch=batch,

                        activity_date=row["activity_date"],

                        scope=row["scope"],

                        category=row["category"],

                        source_type=row["source_type"],

                        raw_quantity=row["raw_quantity"],
                        raw_unit=row["raw_unit"],

                        normalized_quantity=row["normalized_quantity"],
                        normalized_unit=row["normalized_unit"],

                        co2e_kg=row["co2e_kg"],

                        location_code=row.get("location_code", ""),
                        vendor_or_carrier=row.get("vendor_or_carrier", ""),
                        description=row.get("description", ""),
                        source_row_id=row.get("source_row_id", ""),

                        flag_reason=row.get("flag_reason", ""),

                        review_status=review_status,
                    )

                    # -----------------------------------------
                    # AUDIT EVENT
                    # -----------------------------------------

                    AuditEvent.objects.create(
                        record=record,
                        actor=user,
                        action=AuditEvent.ACTION_INGESTED,
                        diff={},
                        note="Record ingested from uploaded source file",
                    )

                    success_count += 1

                except Exception as row_error:

                    import traceback

                    print("========== ROW ERROR ==========")
                    print(row_error)
                    traceback.print_exc()
                    print("================================")

                    error_count += 1

            # -------------------------------------------------
            # UPDATE BATCH
            # -------------------------------------------------

            batch.status = IngestionBatch.STATUS_DONE
            batch.row_count = success_count
            batch.error_count = error_count
            batch.completed_at = timezone.now()

            batch.save()

            # -------------------------------------------------
            # RESPONSE
            # -------------------------------------------------

            return Response({
                "message": "Ingestion completed",
                "batch_id": str(batch.id),
                "records_created": success_count,
                "parse_errors": error_count,
            })

        except Exception as exc:

            import traceback

            traceback.print_exc()

            batch.status = IngestionBatch.STATUS_FAILED
            batch.notes = str(exc)
            batch.completed_at = timezone.now()

            batch.save()

            return Response(
                {"error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )