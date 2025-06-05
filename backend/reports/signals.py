from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DeliveryReport
from .utils import recognize_plate, PlateRecognitionError

@receiver(post_save, sender=DeliveryReport)
def auto_recognize_plate(sender, instance, created, **kwargs):
    updated = False

    if instance.truck_license_plate_image and not instance.licence_plate_truck:
        try:
            plate = recognize_plate(instance.truck_license_plate_image.path)
            instance.licence_plate_truck = plate
            updated = True
        except PlateRecognitionError as e:
            print(f"[Truck Plate Error] {e}")

    if instance.trailer_license_plate_image and not instance.licence_plate_trailer:
        try:
            plate = recognize_plate(instance.trailer_license_plate_image.path)
            instance.licence_plate_trailer = plate
            updated = True
        except PlateRecognitionError as e:
            print(f"[Trailer Plate Error] {e}")

    if updated:
        instance.save(update_fields=["licence_plate_truck", "licence_plate_trailer"])
