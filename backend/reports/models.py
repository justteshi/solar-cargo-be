from django.db import models

class DeliveryReport(models.Model):
    location = models.CharField(max_length=255)
    checking_company = models.CharField(max_length=255)
    supplier = models.CharField(max_length=255)
    delivery_slip_number = models.CharField(max_length=100)
    logistic_company = models.CharField(max_length=255)
    container_number = models.CharField(max_length=100)
    licence_plate_truck = models.CharField(max_length=50)
    licence_plate_trailer = models.CharField(max_length=50)
    weather_conditions = models.CharField(max_length=255)
    comments = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        'auth.User',  # or settings.AUTH_USER_MODEL if using a custom user model
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Delivery Report {self.delivery_slip_number}"