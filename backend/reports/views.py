from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from authentication.permissions import IsAdmin
from datetime import datetime
from .models import DeliveryReport
from .pagination import ReportsResultsSetPagination
from .serializers import DeliveryReportSerializer
from .utils import save_report_to_excel, get_username_from_id, convert_excel_to_pdf
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.conf import settings
import os

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all().order_by('-created_at')
    serializer_class = DeliveryReportSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = ReportsResultsSetPagination

    @extend_schema(
        tags=["Delivery Reports"],
        description="List all delivery reports.",
        responses={200: DeliveryReportSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Create a new delivery report.",
        request=DeliveryReportSerializer,
        responses={201: DeliveryReportSerializer}
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        if response.status_code == 201:
            report_data = response.data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_id = report_data.get('id')  # Assuming response.data contains the report ID
            # Generate file paths
            excel_dir = os.path.join(settings.MEDIA_ROOT, "delivery_reports")
            os.makedirs(excel_dir, exist_ok=True)
            excel_filename = f"delivery_report_{timestamp}.xlsx"
            pdf_filename = f"delivery_report_{timestamp}.pdf"
            excel_path = os.path.join(excel_dir, excel_filename)
            # Save Excel
            user_id = report_data.get('user')
            report_data['user'] = get_username_from_id(user_id)
            save_report_to_excel(report_data, file_path=excel_path)
            # Convert to PDF
            convert_excel_to_pdf(excel_path)
            # Update the DeliveryReport model
            from .models import DeliveryReport  # adjust import as needed
            report_instance = DeliveryReport.objects.get(id=report_id)
            report_instance.excel_report_file = f"delivery_reports/{excel_filename}"
            report_instance.pdf_report_file = f"delivery_reports/{pdf_filename}"
            report_instance.save()

        return response

    @extend_schema(
        tags=["Delivery Reports"],
        description="Retrieve a specific delivery report.",
        responses={200: DeliveryReportSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Update a delivery report.",
        request=DeliveryReportSerializer,
        responses={200: DeliveryReportSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Partially update a delivery report.",
        request=DeliveryReportSerializer,
        responses={200: DeliveryReportSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Delete a delivery report.",
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class HomePageView(TemplateView):
    template_name = 'home.html'


@extend_schema(
    tags=["Download Reports"],
    description="Download the Excel file for a specific delivery report.",
    responses={200: {"type": "file"}, 404: {"description": "Report or file not found"}}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_excel_report(request, report_id):
    try:
        report = DeliveryReport.objects.get(id=report_id)
        file_path = str(report.excel_report_file)  # e.g. "delivery_reports/report_123.xlsx"

        if not default_storage.exists(file_path):
            raise FileNotFoundError

        file = default_storage.open(file_path, 'rb')
        filename = os.path.basename(file_path)
        return FileResponse(file, as_attachment=True, filename=filename)

    except (DeliveryReport.DoesNotExist, FileNotFoundError):
        raise Http404("Excel report not found.")

@extend_schema(
    tags=["Download Reports"],
    description="Download the PDF file for a specific delivery report.",
    responses={200: {"type": "file"}, 404: {"description": "Report or file not found"}}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_pdf_report(request, report_id):
    try:
        report = DeliveryReport.objects.get(id=report_id)
        file_path = str(report.pdf_report_file)  # e.g. "delivery_reports/report_123.pdf"

        if not default_storage.exists(file_path):
            raise FileNotFoundError

        file = default_storage.open(file_path, 'rb')
        filename = os.path.basename(file_path)
        return FileResponse(file, as_attachment=True, filename=filename)

    except (DeliveryReport.DoesNotExist, FileNotFoundError):
        raise Http404("PDF report not found.")