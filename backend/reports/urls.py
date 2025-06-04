from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryReportViewSet,  homepage

router = DefaultRouter()
router.register(r'delivery-reports', DeliveryReportViewSet, basename='deliveryreport')

urlpatterns = [
    path('api/', include(router.urls)),                   # API nested under /api/
    path('', homepage, name='home'),  # Homepage at root of app
]