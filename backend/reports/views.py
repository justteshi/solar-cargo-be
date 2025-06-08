from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from .models import DeliveryReport
from .pagination import ReportsResultsSetPagination
from .serializers import DeliveryReportSerializer
from authentication.permissions import HasUserAPIKey

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all()
    serializer_class = DeliveryReportSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [HasUserAPIKey]
    pagination_class = ReportsResultsSetPagination

    @extend_schema(
        tags=["Delivery Reports"],
        description="List all delivery reports.",
        responses={
            200: DeliveryReportSerializer(many=True)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Create a new delivery report.",
        request=DeliveryReportSerializer,
        responses={
            201: DeliveryReportSerializer
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Retrieve a specific delivery report.",
        responses={
            200: DeliveryReportSerializer
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Update a delivery report.",
        request=DeliveryReportSerializer,
        responses={
            200: DeliveryReportSerializer
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Delivery Reports"],
        description="Partially update a delivery report.",
        request=DeliveryReportSerializer,
        responses={
            200: DeliveryReportSerializer
        }
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