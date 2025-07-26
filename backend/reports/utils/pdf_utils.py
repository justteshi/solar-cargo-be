import tempfile
from pathlib import Path
import subprocess
import logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

logger = logging.getLogger(__name__)

def convert_excel_to_pdf(excel_path):
    excel_path = Path(excel_path)
    pdf_filename = excel_path.with_suffix('.pdf').name
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        local_excel = tmpdir_path / excel_path.name
        with default_storage.open(str(excel_path), 'rb') as f_in, open(local_excel, 'wb') as f_out:
            f_out.write(f_in.read())
        command = [
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(tmpdir_path),
            str(local_excel)
        ]
        result = subprocess.run(command, capture_output=True)
        pdf_path = tmpdir_path / pdf_filename
        if result.returncode != 0 or not pdf_path.exists():
            logger.error(
                "LibreOffice failed or PDF not created.\n"
                f"Command: {' '.join(command)}\n"
                f"Stdout: {result.stdout.decode(errors='replace')}\n"
                f"Stderr: {result.stderr.decode(errors='replace')}"
            )
            raise RuntimeError(
                "LibreOffice failed or PDF not created.\n"
                f"Command: {' '.join(command)}\n"
                f"Stdout: {result.stdout.decode(errors='replace')}\n"
                f"Stderr: {result.stderr.decode(errors='replace')}"
            )
        s3_relative_path = f"{settings.REPORT_PATHS['PDF_SUBDIR']}/{pdf_filename}"
        with open(pdf_path, "rb") as f:
            default_storage.save(s3_relative_path, ContentFile(f.read()))
    return default_storage.url(s3_relative_path)