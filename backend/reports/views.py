from django.shortcuts import render
from rest_framework import viewsets
from .models import DeliveryReport
from .serializers import DeliveryReportSerializer
from rest_framework_api_key.permissions import HasAPIKey
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all()
    serializer_class = DeliveryReportSerializer
    permission_classes = [HasAPIKey]

class HomePageView(TemplateView):
    template_name = 'home.html'