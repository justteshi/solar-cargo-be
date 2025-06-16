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
    # Fixed fields
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
    }

    # Items section (right side, dynamic)
    items_start_row = 9
    items_col_name = 'F'
    items_col_label = 'E'
    items_col_amount_label = 'I'
    items_col_amount = 'J'
    items = data.get("items", [])
    num_items = len(items)

    # Status and comment fields (shifted after items)
    status_fields = [
        'load_secured_status',
        'delivery_without_damages_status',
        'packaging_status',
        'goods_according_status',
        'suitable_machines_status',
        'delivery_slip_status',
        'inspection_report_status',
    ]
    comment_keys = [
        'load_secured_comment',
        'delivery_without_damages_comment',
        'packaging_comment',
        'goods_according_comment',
        'suitable_machines_comment',
        'delivery_slip_comment',
        'inspection_report_comment',
    ]
    status_base_row = 17
    status_col = 'H'
    tick_cols = ['I', 'J', 'K']
    comment_col = 'L'

    # General comments (after status/comments)
    comments_row = status_base_row + num_items + len(status_fields)
    comments_cell = f'A{comments_row}'

    # Images (after comments)
    image_anchor_row = comments_row + 2
    image_map = {
        'truck_license_plate_image': f'A{image_anchor_row}',
        'trailer_license_plate_image': f'E{image_anchor_row}',
    }
    image_start_cell = f'A{image_anchor_row}'
    image_end_cell = f'L{image_anchor_row + 12}'

    # User and date (after images)
    user_row = image_anchor_row + 14
    user_cell = f'D{user_row}'
    date_cell = f'D{user_row + 1}'

    tick = "✓"

    # Load workbook
    if default_storage.exists(file_path):
        with default_storage.open(file_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active
    else:
        with open(template_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active

    # Write fixed fields
    for key, cell in cell_map.items():
        if key in data:
            value = data[key]
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            target_cell = get_top_left_cell(ws, cell)
            ws[target_cell] = value
            if key in ['location', 'checking_company']:
                ws[target_cell].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    # Write items dynamically
    for idx, entry in enumerate(items):
        row = items_start_row + idx
        ws[get_top_left_cell(ws, f'{items_col_label}{row}')] = "Item:"
        ws[get_top_left_cell(ws, f'{items_col_name}{row}')] = entry["item"]["name"]
        ws[get_top_left_cell(ws, f'{items_col_amount_label}{row}')] = "Amount:"
        ws[get_top_left_cell(ws, f'{items_col_amount}{row}')] = entry["quantity"]

    # Write status fields, ticks, and comments in correct columns/rows
    for idx, (status_field, comment_field) in enumerate(zip(status_fields, comment_keys)):
        row = status_base_row + num_items + idx
        value = data.get(status_field, None)
        # Status text
        status_text = "Yes" if value is True else "No" if value is False else ""
        status_cell = get_top_left_cell(ws, f'{status_col}{row}')
        ws[status_cell] = status_text
        ws[status_cell].alignment = Alignment(horizontal='center', vertical='center')
        # Ticks
        for col, cond in zip(tick_cols, [True, False, None]):
            cell = f'{col}{row}'
            target_cell = get_top_left_cell(ws, cell)
            ws[target_cell] = tick if ((value is True and col == 'I') or (value is False and col == 'J') or (
                        value is None and col == 'K')) else ""
            ws[target_cell].alignment = Alignment(horizontal='center', vertical='center')
        # Comments
        comment_value = data.get(comment_field, "")
        comment_cell = get_top_left_cell(ws, f'{comment_col}{row}')
        ws[comment_cell] = comment_value
        ws[comment_cell].alignment = Alignment(wrap_text=True, vertical='top')

    # Write general comments
    if 'comments' in data:
        target_cell = get_top_left_cell(ws, comments_cell)
        ws[target_cell] = data['comments']
        ws[target_cell].alignment = Alignment(wrap_text=True, vertical='top')

    # Add images
    max_width, max_height = get_range_dimensions(ws, image_start_cell, image_end_cell)
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

    # Write user and date
    ws[get_top_left_cell(ws, user_cell)] = data.get('user', '')
    ws[get_top_left_cell(ws, date_cell)] = datetime.now().strftime("%d-%m-%Y")

    # Save
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