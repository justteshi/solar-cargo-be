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
from openpyxl.styles import Alignment
from PIL import Image as PILImage

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


def save_report_to_excel(data, file_path='delivery_report.xlsx', template_path='delivery_report_template.xlsx'):
    cell_map = {
        'location': 'A3',
        'checking_company': 'E3',
        'supplier': 'C9',
        'delivery_slip_number': 'C10',
        'logistic_company': 'C11',
        'container_number': 'C12',
        'licence_plate_truck': 'C13',
        'licence_plate_trailer': 'C14',
        'weather_conditions': 'C15',
        'comments': 'A28',
        'user': 'D49',
    }
    if default_storage.exists(file_path):
        with default_storage.open(file_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active
    else:
        with open(template_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active

        # Write regular fields (excluding status fields)
        for key, cell in cell_map.items():
            if key in data:
                value = data[key]
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                target_cell = get_top_left_cell(ws, cell)
                ws[target_cell] = value
                if key in ['location', 'checking_company']:
                    ws[target_cell].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                elif key == 'user':
                    ws[target_cell].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # Map each status field to its row number in Excel
    status_fields = {
        'load_secured_status': 19,
        'delivery_without_damages_status': 20,
        'packaging_status': 21,
        'goods_according_status': 22,
        'suitable_machines_status': 23,
        'delivery_slip_status': 24,
        'inspection_report_status': 25,
    }

    comment_field_map = {
        'load_secured_status': 'load_secured_comment',
        'delivery_without_damages_status': 'delivery_without_damages_comment',
        'packaging_status': 'packaging_comment',
        'goods_according_status': 'goods_according_comment',
        'suitable_machines_status': 'suitable_machines_comment',
        'delivery_slip_status': 'delivery_slip_comment',
        'inspection_report_status': 'inspection_report_comment',
    }

    tick = "✓"
        # Write status fields as ticks
    for field, row in status_fields.items():
        value = data.get(field, None)
        for col, cond in zip(['I', 'J', 'K'], [True, False, None]):
            cell = f'{col}{row}'
            target_cell = get_top_left_cell(ws, cell)
            if (value is True and col == 'I') or (value is False and col == 'J') or (value is None and col == 'K'):
                ws[target_cell] = tick
                ws[target_cell].alignment = Alignment(horizontal='center', vertical='center')
            else:
                ws[target_cell] = ""
                ws[target_cell].alignment = Alignment(horizontal='center', vertical='center')
        # Write comment in column L for this status field
        comment_key = comment_field_map.get(field)
        if comment_key:
            comment = data.get(comment_key, "")
            comment_cell = get_top_left_cell(ws, f'L{row}')
            ws[comment_cell] = comment if comment else ""
            ws[comment_cell].alignment = Alignment(wrap_text=True, vertical='top')

    start_row = 9
    if "items" in data:
        for idx, entry in enumerate(data["items"]):
            row = start_row + idx
            ws[get_top_left_cell(ws, f'E{row}')] = "Item"
            ws[get_top_left_cell(ws, f'G{row}')] = entry["item"]["name"]
            ws[get_top_left_cell(ws, f'I{row}')] = "Amount"
            ws[get_top_left_cell(ws, f'L{row}')] = entry["quantity"]



    image_map = {
        'truck_license_plate_image': 'A32',
        'trailer_license_plate_image': 'E32',
    }
    max_width, max_height = get_range_dimensions(ws, 'A32', 'L45')
    # Add images
    for img_key, cell in image_map.items():
        url = data.get(img_key)
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                img_bytes = io.BytesIO(response.content)
                pil_img = PILImage.open(img_bytes)
                pil_img.thumbnail((max_width, max_height), PILImage.LANCZOS)
                output_img = io.BytesIO()
                pil_img.save(output_img, format='PNG')
                output_img.seek(0)
                img = XLImage(output_img)
                img.anchor = cell
                ws.add_image(img)

    ws['D50'] = datetime.now().strftime("%Y-%m-%d")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    default_storage.save(file_path, ContentFile(output.read()))


def get_top_left_cell(ws, cell):
    for merged_range in ws.merged_cells.ranges:
        if cell in merged_range:
            return merged_range.start_cell.coordinate
    return cell

def get_range_dimensions(ws, start_cell, end_cell):
    from openpyxl.utils import column_index_from_string, get_column_letter

    start_col = ''.join(filter(str.isalpha, start_cell))
    start_row = int(''.join(filter(str.isdigit, start_cell)))
    end_col = ''.join(filter(str.isalpha, end_cell))
    end_row = int(''.join(filter(str.isdigit, end_cell)))

    total_width = 0
    for col_idx in range(column_index_from_string(start_col), column_index_from_string(end_col) + 1):
        col_letter = get_column_letter(col_idx)
        total_width += (ws.column_dimensions[col_letter].width or 8.43) * 7

    total_height = 0
    for row in range(start_row, end_row + 1):
        total_height += (ws.row_dimensions[row].height or 15) * 0.75

    return int(total_width), int(total_height)