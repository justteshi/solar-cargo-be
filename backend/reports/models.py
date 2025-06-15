from django.contrib.auth import get_user_model
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
    weather_conditions = models.CharField(max_length=255, blank=True)
    comments = models.TextField(blank=True)

    truck_license_plate_image = models.ImageField(
        upload_to='license_plates/truck/',
        null=True,
        blank=True)
    trailer_license_plate_image = models.ImageField(
        upload_to='license_plates/trailer/',
        null=True,
        blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Example Step 3 fields
    load_secured_status = models.BooleanField(null=True, blank=True)
    load_secured_comment = models.TextField(blank=True, null=True)

    goods_according_status = models.BooleanField(null=True, blank=True)
    goods_according_comment = models.TextField(blank=True, null=True)

    packaging_status = models.BooleanField(null=True, blank=True)
    packaging_comment = models.TextField(blank=True, null=True)

    delivery_without_damages_status = models.BooleanField(null=True, blank=True)
    delivery_without_damages_comment = models.TextField(blank=True, null=True)

    suitable_machines_status = models.BooleanField(null=True, blank=True)
    suitable_machines_comment = models.TextField(blank=True, null=True)

    delivery_slip_status = models.BooleanField(null=True, blank=True)
    delivery_slip_comment = models.TextField(blank=True, null=True)

    inspection_report_status = models.BooleanField(null=True, blank=True)
    inspection_report_comment = models.TextField(blank=True, null=True)

    User = get_user_model()
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Delivery Report {self.id}"

class DeliveryReportImage(models.Model):
    delivery_report = models.ForeignKey(DeliveryReport, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='delivery_reports/additional_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Item(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    delivery_report = models.ForeignKey(
        DeliveryReport,
        on_delete=models.CASCADE,
        related_name='items'
    )

    def __str__(self):
        return f"{self.name} x {self.quantity}"