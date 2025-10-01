import os
import logging
from datetime import datetime
from django.conf import settings
from .models import DeliveryReport, Location
from .utils.user_utils import get_username_from_id, get_signature_from_user_id
from .utils.excel_utils import save_report_to_excel
from .utils.pdf_utils import convert_excel_to_pdf

logger = logging.getLogger(__name__)


class ReportFileService:
    """Service for handling report file generation"""

    def __init__(self):
        self.excel_dir = os.path.join(settings.MEDIA_ROOT, "delivery_reports_excel")
        os.makedirs(self.excel_dir, exist_ok=True)

    def generate_filenames(self):
        """Generate timestamped filenames"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return {
            'excel': f"delivery_report_{timestamp}.xlsx",
            'pdf': f"delivery_report_{timestamp}.pdf"
        }

    def generate_excel_path(self, filename):
        """Generate full Excel file path"""
        return f"{settings.REPORT_PATHS['EXCEL_SUBDIR']}/{filename}"

    def generate_files(self, report_data, excel_path):
        """Generate both Excel and PDF files"""
        try:
            save_report_to_excel(report_data, file_path=excel_path)
            convert_excel_to_pdf(excel_path)
            return True
        except Exception as e:
            logger.error(f"File generation failed: {e}")
            raise


class ReportDataService:
    """Service for preparing report data"""

    @staticmethod
    def prepare_report_data(report_data):
        """Prepare report data with user and location info"""
        # Get username
        user_id = report_data.get('user')
        report_data['user'] = get_username_from_id(user_id)
        report_data['user_signature'] = get_signature_from_user_id(user_id)

        gsc_urls = report_data.get("goods_seal_container_proof_urls") or []
        report_data["goods_seal_container_proof_urls"] = [u for u in gsc_urls if u]

        # Get location info
        location_id = report_data.get('location')
        location_obj = Location.objects.filter(id=location_id).first()
        if location_obj:
            report_data['location'] = location_obj.name
            report_data['client_logo'] = str(location_obj.logo.url) if location_obj.logo else None
        else:
            report_data['location'] = ""
            report_data['client_logo'] = None

        return report_data


class ReportUpdateService:
    """Service for updating report with file paths"""

    @staticmethod
    def update_report_files(report_id, excel_filename, pdf_filename):
        try:
            report_instance = DeliveryReport.objects.get(id=report_id)
            report_instance.excel_report_file = f"{settings.REPORT_PATHS['EXCEL_SUBDIR']}/{excel_filename}"
            report_instance.pdf_report_file = f"{settings.REPORT_PATHS['PDF_SUBDIR']}/{pdf_filename}"
            report_instance.save()
            return report_instance
        except DeliveryReport.DoesNotExist:
            logger.error(f"Report with ID {report_id} not found")
            raise
