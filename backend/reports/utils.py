import io
import os
import threading
import time
from datetime import datetime

import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage

# Lock to ensure only one API call at a time
_plate_recognizer_lock = threading.Lock()

class PlateRecognitionError(Exception):
    pass

def recognize_plate(image_path):
    api_key = os.environ.get("PLATE_RECOGNIZER_API_KEY")
    if not api_key:
        raise RuntimeError("❌ Plate Recognizer API key is not set in environment variables.")

    with _plate_recognizer_lock:
        time.sleep(1)  # Wait 1 second before making the API call

        with open(image_path, 'rb') as img_file:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                files={'upload': img_file},
                headers={'Authorization': f'Token {api_key}'}
            )

        if response.status_code not in (200, 201):
            raise PlateRecognitionError(f"❌ API request failed: {response.status_code} - {response.text}")

        data = response.json()
        try:
            plate = data['results'][0]['plate'].upper()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"✅ {timestamp} — License plate recognized successfully: {plate}")
            return plate
        except (KeyError, IndexError):
            raise PlateRecognitionError("❌ No license plate detected in the image.")


def save_report_to_excel(data, file_path='delivery_reports.xlsx', template_path='delivery_report_template.xlsx'):
    cell_map = {
        'location': 'A3',
        'checking_company': 'E3',
        'supplier': 'C9',
        'delivery_slip_number': 'C10',
        'logistic_company': 'C11',
        'container_number': 'C12',
        'licence_plate_truck': 'C13',
        'licence_plate_trailer': 'C14',
        'weather_conditions': 'C15'
        # Add all your fields and their target cells here
    }

    image_map = {
        'truck_license_plate_image': 'A38',  # Cell where you want the image
        # Add more image fields and their target cells if needed
    }

    if default_storage.exists(file_path):
        with default_storage.open(file_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active
    else:
        with open(template_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active

    for key, cell in cell_map.items():
        if key in data:
            ws[cell] = data[key]

    for img_key, cell in image_map.items():
        url = data.get(img_key)
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                img_bytes = io.BytesIO(response.content)
                img = XLImage(img_bytes)
                img.anchor = cell
                ws.add_image(img)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    default_storage.save(file_path, ContentFile(output.read()))