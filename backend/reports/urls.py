from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryReportViewSet, HomePageView

router = DefaultRouter()
router.register(r'delivery-reports', DeliveryReportViewSet, basename='deliveryreport')

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),# Homepage at root of app
    path('api/', include(router.urls)),                   # API nested under /api/
]