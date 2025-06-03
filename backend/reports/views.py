from django.shortcuts import render
from rest_framework import viewsets
from .models import DeliveryReport
from .serializers import DeliveryReportSerializer
from rest_framework_api_key.permissions import HasAPIKey

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all()
    serializer_class = DeliveryReportSerializer
    permission_classes = [HasAPIKey]