from django.contrib.auth import get_user_model
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255)
    location = models.ForeignKey(
        'Location',
        on_delete=models.CASCADE,
        related_name='items',
        null=True,  # <- allow nulls for now
        blank=True
    )

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=150)
    logo = models.ImageField(upload_to='locations/logos/')
    client_name = models.CharField(max_length=512, null=True, blank=True)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    locations = models.ManyToManyField(
        Location,
        related_name='suppliers',
        blank=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class DeliveryReport(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_reports'
    )

    supplier = models.CharField(max_length=255, blank=True, null=True)
    supplier_fk = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_reports_fk'
    )

    checking_company = models.CharField(max_length=255)
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

    proof_of_delivery_image = models.ImageField(
        upload_to='proof_of_delivery/',
        null=True,
        blank=True)

    cmr_image = models.ImageField(
        upload_to='cmr/',
        null=True,
        blank=True)

    excel_report_file = models.FileField(
        upload_to='delivery_reports/',
        null=True,
        blank=True,
        # editable=False
    )
    pdf_report_file = models.FileField(
        upload_to='delivery_reports/PDF files/',
        null=True,
        blank=True,
        # editable=False
    )


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

    items = models.ManyToManyField(Item, through='DeliveryReportItem')

    damage_description = models.TextField(null=True, blank=True)

    User = get_user_model()
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Delivery Report {self.id}"

class DeliveryReportDamageImage(models.Model):
    delivery_report = models.ForeignKey(
        DeliveryReport,
        on_delete=models.CASCADE,
        related_name='damage_images'
    )
    image = models.ImageField(upload_to='damage_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DeliveryReportSlipImage(models.Model):
    delivery_report = models.ForeignKey(
        DeliveryReport,
        on_delete=models.CASCADE,
        related_name='slip_images'
    )
    image = models.ImageField(upload_to='delivery_slip/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class DeliveryReportImage(models.Model):
    delivery_report = models.ForeignKey(DeliveryReport, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='additional_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DeliveryReportItem(models.Model):
    delivery_report = models.ForeignKey(DeliveryReport, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.item.name} x {self.quantity} for report {self.delivery_report.id}"