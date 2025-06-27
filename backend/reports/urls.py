from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryReportViewSet, HomePageView, download_excel_report, download_pdf_report

router = DefaultRouter()
router.register(r'delivery-reports', DeliveryReportViewSet, basename='deliveryreport')

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),# Homepage at root of app
    path('api/', include(router.urls)),# API nested under /api/
    path('download-report/<int:report_id>/excel/', download_excel_report, name='download_excel_report'),
    path('download-report/<int:report_id>/pdf/', download_pdf_report, name='download_pdf_report'),
]