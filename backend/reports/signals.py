import os
import tempfile
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DeliveryReport
from .plate_recognition_utils import recognize_plate, PlateRecognitionError

@receiver(post_save, sender=DeliveryReport)
def auto_recognize_plate(sender, instance, created, **kwargs):
    updated = False

    # Truck plate
    if instance.truck_license_plate_image and not instance.licence_plate_truck:
        try:
            ext = os.path.splitext(instance.truck_license_plate_image.name)[1] or ".jpg"
            with instance.truck_license_plate_image.open('rb') as f:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp_file:
                    tmp_file.write(f.read())
                    tmp_file.flush()
                    plate = recognize_plate(tmp_file.name)
            instance.licence_plate_truck = plate
            updated = True
        except PlateRecognitionError as e:
            print(f"[Truck Plate Error] {e}")

    # Trailer plate
    if instance.trailer_license_plate_image and not instance.licence_plate_trailer:
        try:
            ext = os.path.splitext(instance.trailer_license_plate_image.name)[1] or ".jpg"
            with instance.trailer_license_plate_image.open('rb') as f:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=True) as tmp_file:
                    tmp_file.write(f.read())
                    tmp_file.flush()
                    plate = recognize_plate(tmp_file.name)
            instance.licence_plate_trailer = plate
            updated = True
        except PlateRecognitionError as e:
            print(f"[Trailer Plate Error] {e}")

    if updated:
        instance.save(update_fields=["licence_plate_truck", "licence_plate_trailer"])