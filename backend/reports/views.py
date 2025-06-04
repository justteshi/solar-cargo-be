from django.shortcuts import render
from rest_framework import viewsets
from .models import DeliveryReport
from .serializers import DeliveryReportSerializer
from rest_framework_api_key.permissions import HasAPIKey
from django.http import HttpResponse

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all()
    serializer_class = DeliveryReportSerializer
    permission_classes = [HasAPIKey]


class HomePageView(View):
    def get(self, request):
        return HttpResponse("Hello, this is the homepage.")