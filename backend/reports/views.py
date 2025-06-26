from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from authentication.permissions import IsAdmin
from datetime import datetime
from .models import DeliveryReport
from .pagination import ReportsResultsSetPagination
from .serializers import DeliveryReportSerializer
from .utils import save_report_to_excel, get_username_from_id, convert_excel_to_pdf, get_relative_and_abs_path
from rest_framework.permissions import IsAuthenticated
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
            # Use MEDIA_ROOT for absolute path
            excel_dir = os.path.join(settings.MEDIA_ROOT, "delivery_reports_excel")
            os.makedirs(excel_dir, exist_ok=True)
            file_path = os.path.join(excel_dir, f"delivery_report_{timestamp}.xlsx")
            user_id = report_data.get('user')
            report_data['user'] = get_username_from_id(user_id)
            save_report_to_excel(report_data, file_path=file_path)
            convert_excel_to_pdf(file_path)
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