"""
Image Processing Service

Handles image description generation using Gemini Vision API.
Converts images to semantic text descriptions for the DigitalOcean agent.
"""

import os
from google import genai
from google.genai import types
from .utils import read_local_image


def describe_clothing_item(image_path, api_key=None):
    """
    Generate a semantic description of a clothing item using Gemini Vision.

    Args:
        image_path: Path to the clothing image
        api_key: Google API key (optional, reads from env if not provided)

    Returns:
        str: Description of the clothing item (e.g., "blue denim jeans, straight cut, casual")

    Raises:
        Exception: If API call fails
    """
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)

    # Read the image
    image_bytes, mime_type = read_local_image(image_path)

    # Create the content for Gemini
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(
                    text="""Describe this clothing item concisely in one sentence. Include:
- Type of garment (shirt, pants, jacket, etc.)
- Color(s)
- Material/fabric if visible
- Style/cut (casual, formal, fitted, loose, etc.)
- Any distinctive patterns or features

Format: "[color] [material] [type], [style/cut], [pattern/features]"
Example: "blue denim jeans, straight cut, casual"
Keep it under 20 words."""
                ),
            ],
        )
    ]

    # Configure for text-only response
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["TEXT"],  # Text only, no image generation
        temperature=0.3,  # Lower temperature for more consistent descriptions
    )

    # Generate description
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",  # Using flash model for faster descriptions
        contents=contents,
        config=generate_content_config,
    )

    description = response.text.strip()
    return description


def describe_clothing_items(image_paths, api_key=None):
    """
    Generate descriptions for multiple clothing items.

    Args:
        image_paths: List of paths to clothing images
        api_key: Google API key (optional)

    Returns:
        list[dict]: List of dicts with 'index', 'path', and 'description' for each item

    Example return:
        [
            {"index": 1, "path": "shirt.jpg", "description": "white cotton t-shirt, crew neck"},
            {"index": 2, "path": "jeans.jpg", "description": "blue denim jeans, straight cut"}
        ]
    """
    descriptions = []

    for idx, image_path in enumerate(image_paths, start=1):
        print(f"Analyzing clothing item {idx}/{len(image_paths)}: {os.path.basename(image_path)}")

        try:
            description = describe_clothing_item(image_path, api_key)
            descriptions.append({
                "index": idx,
                "path": image_path,
                "description": description
            })
            print(f"  → {description}")

        except Exception as e:
            print(f"  ✗ Error describing image: {e}")
            # Use filename as fallback description
            fallback_desc = f"clothing item from {os.path.basename(image_path)}"
            descriptions.append({
                "index": idx,
                "path": image_path,
                "description": fallback_desc
            })

    return descriptions
