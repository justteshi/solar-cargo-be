from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryReportViewSet

router = DefaultRouter()
router.register(r'delivery-reports', DeliveryReportViewSet, basename='deliveryreport')

urlpatterns = [
    path('', include(router.urls)),
]