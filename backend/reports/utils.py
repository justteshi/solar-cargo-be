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
from copy import copy
from openpyxl.utils import get_column_letter
from openpyxl.styles.borders import Border, Side
from django.contrib.auth import get_user_model

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
        'comments': 'A27',
        'user': 'D46',
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
        'load_secured_status': 18,
        'delivery_without_damages_status': 19,
        'packaging_status': 20,
        'goods_according_status': 21,
        'suitable_machines_status': 22,
        'delivery_slip_status': 23,
        'inspection_report_status': 24,
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
    items = data.get("items", [])
    # Write only the first 7 items
    for idx, entry in enumerate(items[:7]):
        row = start_row + idx
        ws[get_top_left_cell(ws, f'E{row}')] = "Item"
        ws[get_top_left_cell(ws, f'F{row}')] = entry["item"]["name"]
        ws[get_top_left_cell(ws, f'I{row}')] = "Amount"
        ws[get_top_left_cell(ws, f'J{row}')] = entry["quantity"]

    items = data.get("items", [])
    extra_rows = max(0, len(items) - 7)
    image_row = 29 + extra_rows

    image_map = {
        'truck_license_plate_image': f'A{image_row}',
        'trailer_license_plate_image': f'E{image_row}',
    }
    max_width, max_height = get_range_dimensions(ws, 'A29', 'L42')
    for img_key, cell in image_map.items():
        url = data.get(img_key)
        if url:
            response = requests.get(url)
            if response.status_code == 200:
                img_bytes = io.BytesIO(response.content)
                pil_img = PILImage.open(img_bytes)
                pil_img.thumbnail((max_width, max_height))
                output_img = io.BytesIO()
                pil_img.save(output_img, format='PNG')
                output_img.seek(0)
                img = XLImage(output_img)
                img.anchor = cell
                ws.add_image(img)

    ws['D47'] = datetime.now().strftime("%Y-%m-%d")
    ws['D47'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    default_storage.save(file_path, ContentFile(output.read()))

    # If more than 7 items, append the rest
    if len(items) > 7:
        append_extra_items_to_excel(file_path, items[7:], start_row + 7)

def append_extra_items_to_excel(file_path, extra_items, insert_row):
    with default_storage.open(file_path, 'rb') as f:
        wb = load_workbook(f)
        ws = wb.active

        # Step 1: Store and unmerge affected merged cells
        affected_merges = []
        for rng in list(ws.merged_cells.ranges):
            if rng.min_row >= insert_row:
                affected_merges.append((rng.min_row, rng.min_col, rng.max_row, rng.max_col))
                ws.unmerge_cells(str(rng))

        # Step 2: Insert rows
        ws.insert_rows(insert_row, amount=len(extra_items))

        row_above = insert_row - 1
        for i in range(len(extra_items)):
            copy_row_style(ws, row_above, insert_row + i, min_col=1, max_col=12)

        for i in range(len(extra_items)):
            row = insert_row + i
            # Merge A:B
            ws.merge_cells(f"A{row}:B{row}")
            for col in range(1, 3):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center")
            # Merge C:D
            ws.merge_cells(f"C{row}:D{row}")
            for col in range(3, 5):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center")
            # Merge F:H
            ws.merge_cells(f"F{row}:H{row}")
            for col in range(6, 9):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center")
            # Merge J:L
            ws.merge_cells(f"J{row}:L{row}")
            for col in range(10, 13):
                ws.cell(row=row, column=col).alignment = Alignment(horizontal="center", vertical="center")

        for i in range(len(extra_items)):
            cell = ws.cell(row=insert_row + i, column=12)
            original = cell.border
            cell.border = Border(
                left=original.left,
                right=Side(style="medium"),
                top=original.top,
                bottom=original.bottom,
                diagonal=original.diagonal,
                diagonal_direction=original.diagonal_direction,
                outline=original.outline,
                vertical=original.vertical,
                horizontal=original.horizontal,
            )

        # Step 3: Re-merge cells in new positions
        for min_row, min_col, max_row, max_col in affected_merges:
            new_min_row = min_row + len(extra_items)
            new_max_row = max_row + len(extra_items)
            start_cell = f"{get_column_letter(min_col)}{new_min_row}"
            end_cell = f"{get_column_letter(max_col)}{new_max_row}"
            ws.merge_cells(f"{start_cell}:{end_cell}")

        # Step 4: Write extra items
        for idx, entry in enumerate(extra_items):
            row = insert_row + idx
            ws[get_top_left_cell(ws, f'E{row}')] = "Item"
            ws[get_top_left_cell(ws, f'F{row}')] = entry["item"]["name"]
            ws[get_top_left_cell(ws, f'I{row}')] = "Amount"
            ws[get_top_left_cell(ws, f'J{row}')] = entry["quantity"]

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        with default_storage.open(file_path, 'wb') as f:
            f.write(output.read())

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

def copy_row_style(ws, src_row, dest_row, min_col=1, max_col=12):
    for col in range(min_col, max_col + 1):
        src_cell = ws.cell(row=src_row, column=col)
        dest_cell = ws.cell(row=dest_row, column=col)
        if src_cell.has_style:
            dest_cell.font = copy(src_cell.font)
            dest_cell.border = copy(src_cell.border)
            dest_cell.fill = copy(src_cell.fill)
            dest_cell.number_format = copy(src_cell.number_format)
            dest_cell.protection = copy(src_cell.protection)
            dest_cell.alignment = copy(src_cell.alignment)

def get_username_from_id(user_id):
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
        full_name = user.get_full_name()
        return full_name if full_name.strip() else user.username
    except User.DoesNotExist:
        return "Unknown User"