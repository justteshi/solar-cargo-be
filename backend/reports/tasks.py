"""Celery tasks for report file generation.
This task wraps the heavy synchronous file generation and runs it in a worker process.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_report_files(self, report_id):
    """Generate Excel and PDF files for a delivery report.

    This task accepts a report_id, loads the DeliveryReport from DB, serializes it to a dict,
    then invokes the existing services to produce files and update the DB.
    """
    try:
        # Local imports to avoid heavy work at module import time
        from .services import ReportFileService, ReportDataService, ReportUpdateService
        from .models import DeliveryReport
        from .serializers import DeliveryReportSerializer

        report = DeliveryReport.objects.get(pk=report_id)
        report_data = DeliveryReportSerializer(report).data

        file_service = ReportFileService()
        data_service = ReportDataService()
        update_service = ReportUpdateService()

        # Prepare filenames and paths
        filenames = file_service.generate_filenames()
        excel_filename = filenames['excel']
        pdf_filename = filenames['pdf']
        excel_path = file_service.generate_excel_path(excel_filename)

        # Prepare data (e.g., add user name, signature URL, location info)
        prepared_data = data_service.prepare_report_data(report_data.copy())

        # Generate files (Excel + PDF)
        file_service.generate_files(prepared_data, excel_path)

        # Update DB with generated file paths
        update_service.update_report_files(report_id, excel_filename, pdf_filename)

        logger.info(f"Report files generated for report id={report_id}")
        return True
    except Exception as exc:
        logger.exception(f"Failed to generate report files for report id={report_id}: {exc}")
        raise
