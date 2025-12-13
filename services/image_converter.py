"""
Image format conversion service

Handles conversion of various image formats (including HEIC from iPhones)
to formats supported by Google Gemini.
"""

import os
from pathlib import Path
from typing import Optional
from PIL import Image
import mimetypes

# Register HEIF/HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIF support not available


def detect_image_type(filepath: str) -> str:
    """
    Detect image MIME type from file.

    Args:
        filepath: Path to image file

    Returns:
        MIME type string (e.g., 'image/jpeg')
    """
    # Try mimetypes first
    mime_type, _ = mimetypes.guess_type(filepath)

    # If mimetypes fails, try with PIL
    if not mime_type:
        try:
            with Image.open(filepath) as img:
                format_to_mime = {
                    'JPEG': 'image/jpeg',
                    'PNG': 'image/png',
                    'GIF': 'image/gif',
                    'BMP': 'image/bmp',
                    'WEBP': 'image/webp',
                    'HEIC': 'image/heic',
                    'HEIF': 'image/heif'
                }
                mime_type = format_to_mime.get(img.format, 'image/jpeg')
        except Exception:
            # Default fallback
            mime_type = 'image/jpeg'

    return mime_type


def needs_conversion(mime_type: str) -> bool:
    """
    Check if image format needs conversion for Gemini compatibility.

    Args:
        mime_type: MIME type of the image

    Returns:
        True if conversion needed, False otherwise
    """
    # HEIC/HEIF need conversion (iPhone formats)
    # Other uncommon formats should also be converted
    needs_conv = mime_type.lower() in {
        'image/heic',
        'image/heif',
        'image/tiff',
        'image/x-icon'
    }

    return needs_conv


def convert_to_jpeg(input_path: str, output_path: Optional[str] = None, quality: int = 95) -> str:
    """
    Convert any image format to JPEG.

    Args:
        input_path: Path to input image
        output_path: Optional path for output (defaults to input_path with .jpg extension)
        quality: JPEG quality (1-100, default 95)

    Returns:
        Path to converted JPEG file

    Raises:
        Exception: If conversion fails
    """
    try:
        # Determine output path
        if output_path is None:
            input_file = Path(input_path)
            output_path = str(input_file.with_suffix('.jpg'))

        # Open and convert image
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save as JPEG
            img.save(output_path, 'JPEG', quality=quality, optimize=True)

        return output_path

    except Exception as e:
        raise Exception(f"Failed to convert image to JPEG: {e}")


def process_uploaded_image(filepath: str, force_jpeg: bool = True) -> tuple[str, str]:
    """
    Process an uploaded image, converting if necessary.

    Args:
        filepath: Path to uploaded image
        force_jpeg: If True, convert all images to JPEG for consistency

    Returns:
        Tuple of (processed_filepath, mime_type)
    """
    # Detect image type
    mime_type = detect_image_type(filepath)

    # Check if conversion is needed
    if force_jpeg or needs_conversion(mime_type):
        try:
            # Convert to JPEG
            converted_path = convert_to_jpeg(filepath)

            # Remove original if conversion succeeded and it's different
            if converted_path != filepath and os.path.exists(converted_path):
                try:
                    os.remove(filepath)
                except Exception:
                    pass  # Ignore cleanup errors

            return converted_path, 'image/jpeg'

        except Exception as e:
            # If conversion fails, try to use original
            print(f"Warning: Image conversion failed: {e}")
            return filepath, mime_type

    return filepath, mime_type


def validate_and_prepare_image(filepath: str) -> tuple[str, str]:
    """
    Validate and prepare an image for use with AI APIs.

    This function:
    1. Validates the image can be opened
    2. Detects the format
    3. Converts to JPEG if needed
    4. Returns the final path and MIME type

    Args:
        filepath: Path to image file

    Returns:
        Tuple of (final_filepath, mime_type)

    Raises:
        ValueError: If image is invalid or cannot be processed
    """
    if not os.path.exists(filepath):
        raise ValueError(f"Image file not found: {filepath}")

    try:
        # Validate image can be opened
        with Image.open(filepath) as img:
            img.verify()

        # Re-open (verify closes the file)
        with Image.open(filepath) as img:
            # Check reasonable dimensions
            width, height = img.size
            if width < 10 or height < 10:
                raise ValueError("Image dimensions too small")
            if width > 10000 or height > 10000:
                raise ValueError("Image dimensions too large")

        # Process and potentially convert
        return process_uploaded_image(filepath, force_jpeg=True)

    except Exception as e:
        raise ValueError(f"Invalid image file: {e}")
