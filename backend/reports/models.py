from django.db import models
import os
# from .utils import recognize_plate, PlateRecognitionError

class DeliveryReport(models.Model):
    location = models.CharField(max_length=255)
    checking_company = models.CharField(max_length=255)
    supplier = models.CharField(max_length=255)
    delivery_slip_number = models.CharField(max_length=100)
    logistic_company = models.CharField(max_length=255)
    container_number = models.CharField(max_length=100)
    licence_plate_truck = models.CharField(max_length=50, blank=True)
    licence_plate_trailer = models.CharField(max_length=50, blank=True)
    weather_conditions = models.CharField(max_length=255)
    comments = models.TextField(blank=True)

    truck_license_plate_image = models.ImageField(upload_to='license_plates/truck/', null=True, blank=True)
    trailer_license_plate_image = models.ImageField(upload_to='license_plates/trailer/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Delivery Report {self.delivery_slip_number}"

class DeliveryReportImage(models.Model):
    delivery_report = models.ForeignKey(DeliveryReport, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='delivery_reports/additional_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
