import io
import requests

from datetime import datetime
from pathlib import Path
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

from .image_utils import create_collage_of_images, insert_cmr_delivery_slip_images

ITEMS_PER_PAGE = 7
TICK = "✓"
CELL_MAP = {
    'location': 'A3',
    'checking_company': 'E3',
    'supplier': 'C9',
    'delivery_slip_number': 'C10',
    'logistic_company': 'C11',
    'container_number': 'C12',
    'licence_plate_truck': 'C13',
    'licence_plate_trailer': 'C14',
    'weather_conditions': 'C15',
    'user': 'D44',
}
STATUS_FIELDS = {
    'load_secured_status': 18,
    'delivery_without_damages_status': 19,
    'packaging_status': 20,
    'goods_according_status': 21,
    'suitable_machines_status': 22,
    'delivery_slip_status': 23,
    'inspection_report_status': 24,
}
COMMENT_FIELD_MAP = {
    'load_secured_status': 'load_secured_comment',
    'delivery_without_damages_status': 'delivery_without_damages_comment',
    'packaging_status': 'packaging_comment',
    'goods_according_status': 'goods_according_comment',
    'suitable_machines_status': 'suitable_machines_comment',
    'delivery_slip_status': 'delivery_slip_comment',
    'inspection_report_status': 'inspection_report_comment',
}

def save_report_to_excel(data, file_path=None, template_path='delivery_report_template.xlsx'):
    relative_path, abs_path = get_relative_and_abs_path(file_path, subdir="delivery_reports_excel", ext="xlsx")
    items = data.get("items", [])
    extra_rows = max(0, len(items) - ITEMS_PER_PAGE)
    if default_storage.exists(relative_path):
        with default_storage.open(relative_path, 'rb') as f:
            wb = load_workbook(f)
    elif Path(abs_path).exists():
        with open(abs_path, 'rb') as f:
            wb = load_workbook(f)
    else:
        with open(template_path, 'rb') as f:
            wb = load_workbook(f)
        ws = wb.active
        for key, cell in CELL_MAP.items():
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
    ws = wb.active
    for field, row in STATUS_FIELDS.items():
        value = data.get(field, None)
        for col, cond in zip(['I', 'J', 'K'], [True, False, None]):
            cell = f'{col}{row}'
            target_cell = get_top_left_cell(ws, cell)
            ws[target_cell] = TICK if ((value is True and col == 'I') or (value is False and col == 'J') or (value is None and col == 'K')) else ""
            ws[target_cell].alignment = Alignment(horizontal='center', vertical='center')
        comment_key = COMMENT_FIELD_MAP.get(field)
        if comment_key is not None and comment_key in data:
            comment_cell = f"L{row}"
            top_left_comment_cell = get_top_left_cell(ws, comment_cell)
            ws[top_left_comment_cell] = data[comment_key]
            ws[top_left_comment_cell].alignment = Alignment(wrap_text=True, vertical='top')
            if extra_rows == 0:
                autofit_row_height(ws, top_left_comment_cell, data[comment_key], multiplier=15)
            else:
                offset_row = row + extra_rows
                offset_cell = f"L{offset_row}"
                top_left_offset_cell = get_top_left_cell(ws, offset_cell)
                autofit_row_height(ws, top_left_offset_cell, data[comment_key], multiplier=15)
    write_items_to_excel(ws, items[:ITEMS_PER_PAGE], start_row=9)
    items = data.get("items", [])
    extra_rows = max(0, len(items) - ITEMS_PER_PAGE)
    image_start_row = 28 + extra_rows
    image_end_row = 41 + extra_rows
    image_start_cell = f"A{image_start_row}"
    image_end_cell = f"L{image_end_row}"
    image_urls = [
        data.get('truck_license_plate_image'),
        data.get('trailer_license_plate_image'),
        data.get('proof_of_delivery_image'),
    ]
    image_urls = [url for url in image_urls if url]
    create_collage_of_images(ws, image_urls, image_start_cell, image_end_cell)
    ws['D45'] = datetime.now().strftime("%Y-%m-%d")
    ws['D45'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    default_storage.save(relative_path, ContentFile(output.read()))
    if len(items) > ITEMS_PER_PAGE:
        append_extra_items_to_excel(relative_path, items[ITEMS_PER_PAGE:], 9 + ITEMS_PER_PAGE)
        with default_storage.open(relative_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active
        extra_rows = len(items) - ITEMS_PER_PAGE
    else:
        with default_storage.open(relative_path, 'rb') as f:
            wb = load_workbook(f)
            ws = wb.active
        extra_rows = 0
    comments_row = 26 + extra_rows
    comments_cell = f"A{comments_row}"
    if 'comments' in data:
        ws[comments_cell] = data['comments']
        ws[comments_cell].alignment = Alignment(wrap_text=True, vertical='top')
        autofit_row_height(ws, comments_cell, data['comments'], multiplier=1.5)
    cmr_url = data.get('cmr_image')
    delivery_slip_url = data.get('delivery_slip_image')
    if cmr_url or delivery_slip_url:
        insert_cmr_delivery_slip_images(ws, cmr_url, delivery_slip_url)

    additional_images = data.get('additional_images_urls', [])
    for idx, img_data in enumerate(additional_images, start=1):
        url = img_data.get('image')
        if not url:
            continue
        try:
            response = requests.get(url)
            response.raise_for_status()
            img_bytes = io.BytesIO(response.content)
            img_ws = wb.create_sheet(title=f"Additional Image {idx}")
            xl_img = XLImage(img_bytes)
            xl_img.anchor = "A1"
            img_ws.add_image(xl_img)
            img_ws.page_setup.orientation = "portrait"
            img_ws.page_setup.paperSize = img_ws.PAPERSIZE_A4
            img_ws.page_setup.fitToWidth = 1
            img_ws.page_setup.fitToHeight = 1
            img_ws.page_setup.fitToPage = True
            img_ws.page_setup.scale = None
        except Exception as e:
            # Optionally log error
            pass
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    with default_storage.open(relative_path, 'wb') as f:
        f.write(output.read())
    return abs_path

def write_items_to_excel(ws, items, start_row):
    for idx, entry in enumerate(items):
        row = start_row + idx
        ws[get_top_left_cell(ws, f'E{row}')] = "Item"
        ws[get_top_left_cell(ws, f'F{row}')] = entry["item"]["name"]
        ws[get_top_left_cell(ws, f'I{row}')] = "Amount"
        ws[get_top_left_cell(ws, f'J{row}')] = entry["quantity"]

def append_extra_items_to_excel(file_path, extra_items, insert_row):
    from openpyxl.styles.borders import Border, Side
    with default_storage.open(file_path, 'rb') as f:
        wb = load_workbook(f)
        ws = wb.active
        affected_merges = []
        for rng in list(ws.merged_cells.ranges):
            if rng.min_row >= insert_row:
                affected_merges.append((rng.min_row, rng.min_col, rng.max_row, rng.max_col))
                ws.unmerge_cells(str(rng))
        ws.insert_rows(insert_row, amount=len(extra_items))
        row_above = insert_row - 1
        for i in range(len(extra_items)):
            copy_row_style(ws, row_above, insert_row + i, min_col=1, max_col=12)
        for i in range(len(extra_items)):
            row = insert_row + i
            ws.merge_cells(f"A{row}:B{row}")
            ws.merge_cells(f"C{row}:D{row}")
            ws.merge_cells(f"F{row}:H{row}")
            ws.merge_cells(f"J{row}:L{row}")
            cell = ws.cell(row=row, column=12)
            original = cell.border
            cell.border = Border(
                left=original.left,
                right=Side(style="thick"),
                top=original.top,
                bottom=original.bottom,
                diagonal=original.diagonal,
                diagonal_direction=original.diagonal_direction,
                outline=original.outline,
                vertical=original.vertical,
                horizontal=original.horizontal,
            )
        for min_row, min_col, max_row, max_col in affected_merges:
            new_min_row = min_row + len(extra_items)
            new_max_row = max_row + len(extra_items)
            start_cell = f"{get_column_letter(min_col)}{new_min_row}"
            end_cell = f"{get_column_letter(max_col)}{new_max_row}"
            ws.merge_cells(f"{start_cell}:{end_cell}")
        write_items_to_excel(ws, extra_items, insert_row)
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        with default_storage.open(file_path, 'wb') as f:
            f.write(output.read())

def copy_row_style(ws, src_row, dest_row, min_col=1, max_col=12):
    from copy import copy
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

def get_top_left_cell(ws, cell):
    for merged_range in ws.merged_cells.ranges:
        if cell in merged_range:
            return merged_range.start_cell.coordinate
    return cell

def autofit_row_height(ws, cell, text, multiplier=14):
    col_letter = ''.join(filter(str.isalpha, cell))
    row_num = int(''.join(filter(str.isdigit, cell)))
    col_width = ws.column_dimensions[col_letter].width or 8.43
    chars_per_line = int(col_width * 1.15)
    text = (text or "").rstrip()
    total_lines = 0
    for line in text.split('\n'):
        line = line.rstrip()
        if not line:
            total_lines += 1
        else:
            total_lines += (len(line) - 1) // chars_per_line + 1
    ws.row_dimensions[row_num].height = max(15, total_lines * multiplier)

def get_relative_and_abs_path(file_path=None, subdir="delivery_reports_excel", ext="xlsx"):
    if file_path:
        abs_path = Path(file_path)
        relative_path = abs_path.relative_to(settings.MEDIA_ROOT)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relative_path = Path(subdir) / f"delivery_report_{timestamp}.{ext}"
        abs_path = Path(settings.MEDIA_ROOT) / relative_path
    return str(relative_path), str(abs_path)