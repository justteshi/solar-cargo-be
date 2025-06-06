from rest_framework import viewsets
from .models import DeliveryReport
from .serializers import DeliveryReportSerializer
from authentication.permissions import HasUserAPIKey
from django.views.generic import TemplateView
from rest_framework.parsers import MultiPartParser, FormParser

class DeliveryReportViewSet(viewsets.ModelViewSet):
    queryset = DeliveryReport.objects.all()
    serializer_class = DeliveryReportSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [HasUserAPIKey]

class HomePageView(TemplateView):
    template_name = 'home.html'