"""
Utility functions for image handling

Extracted from outfit_image_gen.py for reusability across services.
"""

import mimetypes
import os


def read_local_image(image_path):
    """
    Reads a local image file and returns the bytes and mime type.

    Args:
        image_path: Path to the image file

    Returns:
        tuple: (image_bytes, mime_type)

    Raises:
        FileNotFoundError: If the image doesn't exist
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Could not find image at: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # Default fallback

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    return image_bytes, mime_type


def save_binary_file(file_name, data):
    """
    Saves binary data to a file.

    Args:
        file_name: Path where the file should be saved
        data: Binary data to write

    Returns:
        str: The file path where data was saved
    """
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")
    return file_name


def validate_image_path(image_path):
    """
    Validates that an image path exists and is a valid image format.

    Args:
        image_path: Path to validate

    Returns:
        bool: True if valid

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a valid image format
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    _, ext = os.path.splitext(image_path.lower())

    if ext not in valid_extensions:
        raise ValueError(f"Invalid image format: {ext}. Supported: {valid_extensions}")

    return True


def validate_image_paths(image_paths, max_count=20):
    """
    Validates a list of image paths.

    Args:
        image_paths: List of image paths to validate
        max_count: Maximum number of images allowed (default: 20)

    Returns:
        bool: True if all paths are valid

    Raises:
        ValueError: If constraints are violated
    """
    if not image_paths:
        raise ValueError("No images provided")

    if len(image_paths) > max_count:
        raise ValueError(f"Too many images. Maximum: {max_count}, provided: {len(image_paths)}")

    for path in image_paths:
        validate_image_path(path)

    return True
