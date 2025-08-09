import os
import logging

import magic

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    pass

# Allowed image MIME types and extensions
ALLOWED_IMAGE_MIMETYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp',
    'image/tiff'
}

ALLOWED_IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif',
    '.bmp', '.webp', '.tiff', '.tif'
}

# MIME type to extension mapping
MIME_TO_EXTENSION = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/bmp': ['.bmp'],
    'image/webp': ['.webp'],
    'image/tiff': ['.tiff', '.tif']
}

def validate_image_file(file_obj):
    """
    Validate uploaded image file for security and type checking.
    """
    if not file_obj:
        logger.error("No file provided for image validation.")
        raise FileValidationError("No file provided")

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_obj.size > max_size:
        logger.error(f"File too large: {file_obj.size} bytes. Max size is {max_size} bytes.")
        raise FileValidationError(f"File too large. Maximum size is {max_size // (1024*1024)}MB")

    # Get file extension from name
    file_name = getattr(file_obj, 'name', '')
    if not file_name:
        logger.error("File must have a name for validation.")
        raise FileValidationError("File must have a name")

    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        logger.error(f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")
        raise FileValidationError(f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    # Read file content for MIME type detection
    file_obj.seek(0)
    file_content = file_obj.read(8192)  # Read first 8KB for analysis
    file_obj.seek(0)  # Reset file pointer

    # Detect MIME type using python-magic
    try:
        detected_mime = magic.from_buffer(file_content, mime=True)
    except Exception as e:
        logger.error(f"Could not detect file type: {e}")
        raise FileValidationError(f"Could not detect file type: {e}")

    # Validate MIME type
    if detected_mime not in ALLOWED_IMAGE_MIMETYPES:
        logger.error(f"Invalid file type: {detected_mime}. Must be an image file.")
        raise FileValidationError(f"Invalid file type: {detected_mime}. Must be an image file")

    # Cross-validate extension with MIME type
    expected_extensions = MIME_TO_EXTENSION.get(detected_mime, [])
    if ext not in expected_extensions:
        logger.error(
            f"File extension {ext} doesn't match detected type {detected_mime}. "
            f"Expected extensions: {', '.join(expected_extensions)}"
        )
        raise FileValidationError(
            f"File extension {ext} doesn't match detected type {detected_mime}. "
            f"Expected extensions: {', '.join(expected_extensions)}"
        )

    # Additional security checks for image headers
    if not _validate_image_headers(file_content, detected_mime):
        logger.error("File appears to be corrupted or not a valid image.")
        raise FileValidationError("File appears to be corrupted or not a valid image")
    return True

def _validate_image_headers(file_content, mime_type):
    """
    Validate image file headers for basic integrity checks.
    """
    if len(file_content) < 10:
        return False

    # Check common image file signatures
    signatures = {
        'image/jpeg': [b'\xff\xd8\xff'],
        'image/png': [b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'],
        'image/gif': [b'GIF87a', b'GIF89a'],
        'image/bmp': [b'BM'],
        'image/webp': [b'RIFF', b'WEBP'],
        'image/tiff': [b'II*\x00', b'MM\x00*']
    }

    expected_sigs = signatures.get(mime_type, [])
    for sig in expected_sigs:
        if file_content.startswith(sig):
            return True
        # For WEBP, check both RIFF and WEBP signatures
        if mime_type == 'image/webp' and b'RIFF' in file_content[:12] and b'WEBP' in file_content[:12]:
            return True

    return False