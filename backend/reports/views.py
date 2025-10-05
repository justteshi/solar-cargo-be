import base64
import logging
import os
import tempfile
import mimetypes

from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter, inline_serializer
from rest_framework import serializers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DeliveryReport, Item, Location, Supplier
from .pagination import ReportsResultsSetPagination
from .serializers import (
    DeliveryReportSerializer,
    ItemSerializer,
    ItemAutocompleteFilterSerializer,
    SupplierAutocompleteSerializer
)
from .services import ReportFileService, ReportDataService, ReportUpdateService
from .utils.plate_recognition_utils import recognize_plate, PlateRecognitionError

logger = logging.getLogger(__name__)


class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all().order_by('-created_at')
    serializer_class = DeliveryReportSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
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
            try:
                self._handle_file_generation(response.data)
            except Exception as e:
                logger.error(f"File generation failed: {e}")
                return Response(
                    {"error": "Failed to generate report files"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return response

    def _handle_file_generation(self, report_data):
        """Handle the complete file generation workflow"""
        report_id = report_data.get('id')

        # Initialize services
        file_service = ReportFileService()
        data_service = ReportDataService()
        update_service = ReportUpdateService()

        # Generate filenames and paths
        filenames = file_service.generate_filenames()
        excel_path = file_service.generate_excel_path(filenames['excel'])

        # Prepare report data
        prepared_data = data_service.prepare_report_data(report_data.copy())

        # Generate files
        file_service.generate_files(prepared_data, excel_path)

        # Update database
        update_service.update_report_files(
            report_id,
            filenames['excel'],
            filenames['pdf']
        )

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
        OpenApiParameter(name='q', description='Search term', required=False, type=str),
        OpenApiParameter(name='location', description='Location filter', required=False, type=str),
    ],
    responses=ItemSerializer(many=True),
)
class ItemAutocompleteView(ListAPIView):
    serializer_class = ItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query_params = ItemAutocompleteFilterSerializer(data=self.request.GET)
        query_params.is_valid(raise_exception=True)

        q = query_params.validated_data.get('q', None)
        location = query_params.validated_data.get('location', None)

        queryset = Item.objects.all()
        if q:
            queryset = queryset.filter(name__icontains=q)

        if location:
            queryset = queryset.filter(location=location)

        return queryset.order_by('name')[:10]


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


def encode_file(file_field, filename):
    """
    Encode a file into base64 format.
    """
    try:
        with file_field.open('rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        return {
            "filename": filename,
            "content": encoded
        }
    except Exception as e:
        logging.error(f"Error encoding file {filename}: {e}")
        return None

def guess_content_type(filename, default="image/jpeg"):
    return mimetypes.guess_type(filename)[0] or default


@extend_schema(
    operation_id="download_delivery_report_media_base64",
    summary="Download delivery report media as base64",
    tags=["Download Report Media"],
    description="Download all media files (images) associated with a delivery report as base64-encoded data",
    parameters=[
        OpenApiParameter(
            name="report_id",
            description="ID of the delivery report",
            required=True,
            type=int,
            location=OpenApiParameter.PATH,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='MediaDownloadResponse',
                fields={
                    'media_data': serializers.DictField(
                        child=serializers.ListField(
                            child=inline_serializer(
                                name='MediaFile',
                                fields={
                                    'filename': serializers.CharField(),
                                    'data': serializers.CharField(help_text="Base64 encoded file data"),
                                    'content_type': serializers.CharField(),
                                }
                            )
                        ),
                        help_text="Dictionary with media categories as keys and lists of base64-encoded files as values"
                    ),
                    'total_files': serializers.IntegerField(help_text="Total number of files included"),
                }
            ),
            description="Base64-encoded media files organized by category",
        ),
        404: OpenApiResponse(description="Delivery report not found"),
    },
    examples=[
        OpenApiExample(
            "Successful response",
            value={
                "media_data": {
                    "license_plates": [
                        {
                            "filename": "truck_license.jpg",
                            "data": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
                            "content_type": "image/jpeg"
                        }
                    ],
                    "damage_images": [
                        {
                            "filename": "damage_001.png",
                            "data": "iVBORw0KGgoAAAANSUhEUgAA...",
                            "content_type": "image/png"
                        }
                    ]
                },
                "total_files": 2
            }
        )
    ]
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_report_media(request, report_id):
    """
    Return media files as base64-encoded JSON, including all images associated with the report.
    """
    try:
        report = DeliveryReport.objects.get(pk=report_id)
    except DeliveryReport.DoesNotExist:
        return JsonResponse({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

    media_data = {}

    # Truck license plate image
    if report.truck_license_plate_image:
        encoded = encode_file(report.truck_license_plate_image, "truck_license_plate.jpg")
        if encoded:
            media_data.setdefault('license_plates', []).append({
                **encoded,
                "content_type": "image/jpeg"
            })

    # Trailer license plate image
    if report.trailer_license_plate_image:
        encoded = encode_file(report.trailer_license_plate_image, "trailer_license_plate.jpg")
        if encoded:
            media_data.setdefault('license_plates', []).append({
                **encoded,
                "content_type": "image/jpeg"
            })

    # Proof of delivery image
    if report.proof_of_delivery_image:
        encoded = encode_file(report.proof_of_delivery_image, "proof_of_delivery.jpg")
        if encoded:
            media_data['delivery_proof'] = [{
                **encoded,
                "content_type": "image/jpeg"
            }]

    # CMR image
    if report.cmr_image:
        encoded = encode_file(report.cmr_image, "cmr.jpg")
        if encoded:
            media_data['cmr'] = [{
                **encoded,
                "content_type": "image/jpeg"
            }]

    # Multiple files
    gsc_files = []
    for i, img in enumerate(report.gsc_proof_images.all().order_by("id")):
        filename = f"gsc_{i}{os.path.splitext(img.image.name)[1] or '.jpg'}"
        encoded = encode_file(img.image, filename)
        if encoded:
            gsc_files.append({
                **encoded,
                "content_type": guess_content_type(filename)
            })
    if gsc_files:
        media_data["gsc_proof"] = gsc_files

    slip_images = []
    for i, img in enumerate(report.slip_images.all()):
        encoded = encode_file(img.image, f"slip_{i}.jpg")
        if encoded:
            slip_images.append({
                **encoded,
                "content_type": "image/jpeg"
            })
    if slip_images:
        media_data['delivery_slips'] = slip_images

    damage_images = []
    for i, img in enumerate(report.damage_images.all()):
        encoded = encode_file(img.image, f"damage_{i}.jpg")
        if encoded:
            damage_images.append({
                **encoded,
                "content_type": "image/jpeg"
            })
    if damage_images:
        media_data['damage_images'] = damage_images

    additional_images = []
    for i, img in enumerate(report.additional_images.all()):
        encoded = encode_file(img.image, f"additional_{i}.jpg")
        if encoded:
            additional_images.append({
                **encoded,
                "content_type": "image/jpeg"
            })
    if additional_images:
        media_data['additional'] = additional_images

    return JsonResponse({
        "media_data": media_data,
        "total_files": sum(len(files) for files in media_data.values())
    }, status=status.HTTP_200_OK)


@extend_schema(
    operation_id="download_single_media_file",  # Add unique operation_id
    tags=["Download Reports"],
    description="Download a specific media file from a delivery report.",
    parameters=[
        OpenApiParameter(
            name='report_id',
            description='Delivery report ID',
            required=True,
            type=int,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name='file_type',
            description='Type of file to download',
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        ),
    ],
    responses={
        200: OpenApiResponse(response={"type": "file"}, description="Media file"),
        404: OpenApiResponse(description="File not found")
    }
)
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
    permission_classes = [IsAuthenticated]

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
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                with uploaded_file.open('rb') as f:
                    temp_file.write(f.read())
                temp_file_path = temp_file.name

            try:
                return recognize_plate(temp_file_path)
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

        try:
            truck_plate = process_uploaded_image(truck_image)
            trailer_plate = process_uploaded_image(trailer_image)

            return Response({
                "truck_plate": truck_plate,
                "trailer_plate": trailer_plate
            })
        except PlateRecognitionError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
