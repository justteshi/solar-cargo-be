import os
import tempfile
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.http import FileResponse, Http404
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter, inline_serializer
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework import status

from authentication.permissions import IsAdmin

from datetime import datetime
from .models import DeliveryReport, Item, Location, Supplier
from .pagination import ReportsResultsSetPagination
from .utils.main_utils import get_username_from_id
from .utils.excel_utils import save_report_to_excel
from .utils.pdf_utils import convert_excel_to_pdf
from .utils.plate_recognition_utils import recognize_plate, PlateRecognitionError

from .serializers import (
    DeliveryReportSerializer,
    ItemSerializer,
    ItemAutocompleteFilterSerializer,
    LocationSerializer, SupplierAutocompleteSerializer
)
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
            # Get the username and location from the user ID
            user_id = report_data.get('user')
            report_data['user'] = get_username_from_id(user_id)
            location_id = report_data.get('location')
            location_obj = Location.objects.filter(id=location_id).first()
            if location_obj:
                report_data['location'] = location_obj.name
                report_data['client_logo'] = str(location_obj.logo.url) if location_obj.logo else None
            else:
                report_data['location'] = ""
                report_data['client_logo'] = None
            # Save Excel
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
    parameters=[
        OpenApiParameter(name="location_id",
                         location=OpenApiParameter.PATH,
                         required=True,
                         type=int,
                         description="Location ID")
    ],
    responses=DeliveryReportSerializer(many=True),
    tags=["Locations"]
)
class ReportsByLocationView(ListAPIView):
    serializer_class = DeliveryReportSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ReportsResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, 'profile', None)

        if not profile:
            return DeliveryReport.objects.none()

        location = get_object_or_404(Location, id=self.kwargs['location_id'])

        if location not in profile.locations.all():
            return DeliveryReport.objects.none()

        return DeliveryReport.objects.filter(location=location).order_by('-id')


class RecognizePlatesView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=inline_serializer(
            name='PlateRecognitionRequest',
            fields={
                'truck_plate_image': serializers.ImageField(),
                'trailer_plate_image': serializers.ImageField(),
            }
        ),
        responses={
            200: inline_serializer(
                name='PlateRecognitionResponse',
                fields={
                    'truck_plate': serializers.CharField(allow_null=True),
                    'trailer_plate': serializers.CharField(allow_null=True),
                }
            ),
            400: OpenApiResponse(description="Missing or invalid input"),
            500: OpenApiResponse(description="Plate recognition error"),
        },
        tags=["Plate Recognition"],
        description="Recognize truck and trailer license plates from uploaded images.",
        examples=[
            OpenApiExample(
                name="Successful Recognition",
                value={"truck_plate": "CA1234AC", "trailer_plate": "TX9876XY"},
                response_only=True
            )
        ]
    )
    def post(self, request):
        truck_image = request.FILES.get("truck_plate_image")
        trailer_image = request.FILES.get("trailer_plate_image")

        if not truck_image or not trailer_image:
            return Response(
                {"error": "Both truck_plate_image and trailer_plate_image are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        def process_uploaded_image(uploaded_file):
            ext = os.path.splitext(uploaded_file.name)[1] or ".jpg"
            with uploaded_file.open('rb') as f:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp_file:
                    tmp_file.write(f.read())
                    tmp_file.flush()
                    return recognize_plate(tmp_file.name)

        try:
            truck_plate = process_uploaded_image(truck_image)
        except PlateRecognitionError as e:
            truck_plate = None
            print(f"[Truck Plate Error] {e}")

        try:
            trailer_plate = process_uploaded_image(trailer_image)
        except PlateRecognitionError as e:
            trailer_plate = None
            print(f"[Trailer Plate Error] {e}")

        return Response({
            "truck_plate": truck_plate,
            "trailer_plate": trailer_plate,
        })

class SupplierAutocompleteView(ListCreateAPIView):
    serializer_class = SupplierAutocompleteSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Suppliers"],
        parameters=[
            OpenApiParameter(
                name="location_id",
                description="Location identifier",
                required=True,
                location=OpenApiParameter.PATH,
                type=int
            ),
            OpenApiParameter(
                name="q",
                description="Search term",
                required=False,
                location=OpenApiParameter.QUERY,
                type=str
            ),
        ],
        responses={200: SupplierAutocompleteSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        loc = Location.objects.filter(pk=self.kwargs['location_id']).first()
        if not loc:
            return Supplier.objects.none()

        qs = Supplier.objects.filter(locations=loc)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by('name')[:10]