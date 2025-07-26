import mimetypes
import magic
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import os

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
        raise FileValidationError("No file provided")

    # Check file size (50MB limit)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_obj.size > max_size:
        raise FileValidationError(f"File too large. Maximum size is {max_size // (1024*1024)}MB")

    # Get file extension from name
    file_name = getattr(file_obj, 'name', '')
    if not file_name:
        raise FileValidationError("File must have a name")

    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise FileValidationError(f"Invalid file extension: {ext}. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    # Read file content for MIME type detection
    file_obj.seek(0)
    file_content = file_obj.read(8192)  # Read first 8KB for analysis
    file_obj.seek(0)  # Reset file pointer

    # Detect MIME type using python-magic
    try:
        detected_mime = magic.from_buffer(file_content, mime=True)
    except Exception as e:
        raise FileValidationError(f"Could not detect file type: {e}")

    # Validate MIME type
    if detected_mime not in ALLOWED_IMAGE_MIMETYPES:
        raise FileValidationError(f"Invalid file type: {detected_mime}. Must be an image file")

    # Cross-validate extension with MIME type
    expected_extensions = MIME_TO_EXTENSION.get(detected_mime, [])
    if ext not in expected_extensions:
        raise FileValidationError(
            f"File extension {ext} doesn't match detected type {detected_mime}. "
            f"Expected extensions: {', '.join(expected_extensions)}"
        )

    # Additional security checks for image headers
    if not _validate_image_headers(file_content, detected_mime):
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

def validate_file_name(filename):
    """
    Validate filename for security issues.
    """
    if not filename:
        raise FileValidationError("Filename cannot be empty")

    if len(filename) > 255:
        raise FileValidationError("Filename too long (max 255 characters)")

    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        if char in filename:
            raise FileValidationError(f"Filename contains invalid character: {char}")

    # Check for reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3',
        'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6',
        'LPT7', 'LPT8', 'LPT9'
    }
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        raise FileValidationError(f"Filename uses reserved name: {filename}")

    return True