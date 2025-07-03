import os
import boto3
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import DeliveryReport, DeliveryReportImage
from authentication.permissions import IsAdmin

from datetime import datetime
from .models import DeliveryReport, Item, Location, LocationAssignment
from .pagination import ReportsResultsSetPagination
from .utils.main_utils import get_username_from_id
from .utils.excel_utils import save_report_to_excel
from .utils.pdf_utils import convert_excel_to_pdf

from .serializers import DeliveryReportSerializer, ItemSerializer, ItemAutocompleteFilterSerializer, LocationSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all().order_by('-created_at')
    serializer_class = DeliveryReportSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = ReportsResultsSetPagination
    http_method_names = ['get', 'post', 'put', 'patch']

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
            # Use MEDIA_ROOT for absolute path
            excel_dir = os.path.join(settings.MEDIA_ROOT, "delivery_reports_excel")
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
            report_instance.excel_report_file = f"delivery_reports_excel/{excel_filename}"
            report_instance.pdf_report_file = f"delivery_reports_pdf/{pdf_filename}"
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
    tags=["Items"],
    parameters=[
        OpenApiParameter(name='q', description='Search term', required=True, type=str),
    ],
    responses=ItemSerializer(many=True),
)
class ItemAutocompleteView(ListAPIView):
    serializer_class = ItemSerializer
    permission_classes = [AllowAny] # Can be set IsAuthenticated if needed

    def get_queryset(self):
        query_params = ItemAutocompleteFilterSerializer(data=self.request.GET)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data['q']
        return Item.objects.filter(name__icontains=query).order_by('name')[:10]


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
    except DeliveryReport.DoesNotExist:
        raise Http404("Report not found.")

    file_path = str(report.excel_report_file)
    if not file_path or not default_storage.exists(file_path):
        raise Http404("Excel file not found.")

    file = default_storage.open(file_path, 'rb')
    filename = os.path.basename(file_path)
    return FileResponse(file, as_attachment=True, filename=filename)


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
    except DeliveryReport.DoesNotExist:
        raise Http404("Report not found.")

    file_path = str(report.pdf_report_file)
    if not file_path or not default_storage.exists(file_path):
        raise Http404("PDF file not found.")

    file = default_storage.open(file_path, 'rb')
    filename = os.path.basename(file_path)
    return FileResponse(file, as_attachment=True, filename=filename)

@extend_schema(
    tags=["Media"],
    description="Proxy endpoint to securely serve all delivery report images (including additional images) except report files. Requires authentication.",
    responses={200: {"type": "file"}, 404: {"description": "File not found"}}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def delivery_report_media_file_proxy(request, report_id, file_field, additional_image_id=None):
    allowed_fields = [
        "cmr_image",
        "proof_of_delivery_image",
        "delivery_slip_image",
        "truck_license_plate_image",
        "trailer_license_plate_image",
    ]

    if file_field == "additional_image":
        if not additional_image_id:
            raise Http404("Additional image ID required.")
        try:
            image_obj = DeliveryReportImage.objects.get(id=additional_image_id, delivery_report_id=report_id)
            s3_key = image_obj.image.name
        except DeliveryReportImage.DoesNotExist:
            raise Http404("Additional image not found.")
    elif file_field in allowed_fields:
        try:
            report = DeliveryReport.objects.get(id=report_id)
            file_field_obj = getattr(report, file_field, None)
            if not file_field_obj or not file_field_obj.name:
                raise Http404("File not found.")
            s3_key = file_field_obj.name
        except DeliveryReport.DoesNotExist:
            raise Http404("Report not found.")
    else:
        raise Http404("Invalid file type.")

    s3 = boto3.client('s3')
    try:
        obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
        return FileResponse(obj['Body'], content_type=obj['ContentType'])
    except Exception:
        raise Http404("File not found in S3.")

class MyLocationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        assigned_locations = Location.objects.filter(
            id__in=LocationAssignment.objects.filter(user=request.user).values_list('location_id', flat=True)
        )
        serializer = LocationSerializer(assigned_locations, many=True)
        return Response(serializer.data)

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='location_id',
            description='ID of the Location',
            required=True,
            type=int,
            location=OpenApiParameter.PATH
        )
    ],
    responses={200: DeliveryReportSerializer(many=True)},
    tags=["Delivery Reports"]
)
class ReportsByLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, location_id):
        location = get_object_or_404(Location, id=location_id)

        if not LocationAssignment.objects.filter(user=request.user, location=location).exists():
            return Response({"detail": "Not authorized for this location."}, status=403)

        reports = DeliveryReport.objects.filter(location_logo=location)
        serializer = DeliveryReportSerializer(reports, many=True)
        return Response(serializer.data)
