from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import download_excel_report, download_pdf_report, delivery_report_media_file_proxy
from .views import DeliveryReportViewSet, HomePageView, ItemAutocompleteView, MyLocationsView, ReportsByLocationView

router = DefaultRouter()
router.register(r'delivery-reports', DeliveryReportViewSet, basename='deliveryreport')

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),# Homepage at root of app
    path('api/', include(router.urls)),# API nested under /api/
    path('api/items/autocomplete/', ItemAutocompleteView.as_view(), name='item-autocomplete'),
    path('download-report/<int:report_id>/excel/', download_excel_report, name='download_excel_report'),
    path('download-report/<int:report_id>/pdf/', download_pdf_report, name='download_pdf_report'),
    path('my-locations/', MyLocationsView.as_view(), name='my-locations'),
    path('reports-by-location/<int:location_id>/', ReportsByLocationView.as_view(), name='reports-by-location'),
    path('media-proxy/report/<int:report_id>/<str:file_field>/', delivery_report_media_file_proxy, name='delivery-report-file-proxy'),
    path('media-proxy/report/<int:report_id>/<str:file_field>/<int:additional_image_id>/', delivery_report_media_file_proxy, name='delivery-report-additional-image-proxy'),
]