"""
Image Processing Service

Handles image description generation using Gemini Vision API.
Converts images to semantic text descriptions for the DigitalOcean agent.
"""

import os
import time
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
        model="gemini-2.5-flash-image",  # Higher quota limits for image understanding
        contents=contents,
        config=generate_content_config,
    )

    description = response.text.strip()
    return description


def describe_person_appearance(selfie_path, api_key=None):
    """
    Generate a detailed description of a person's appearance from a selfie.

    Args:
        selfie_path: Path to the selfie image
        api_key: Google API key (optional, reads from env if not provided)

    Returns:
        str: Description of the person's appearance for fashion styling

    Raises:
        Exception: If API call fails
    """
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

    client = genai.Client(api_key=api_key)

    # Read the selfie image
    image_bytes, mime_type = read_local_image(selfie_path)

    # Create the content for Gemini
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(
                    text="""Describe this person's physical appearance AND current outfit for fashion styling purposes.

PART 1 - Person's Appearance:
- Apparent gender presentation (male-presenting, female-presenting, androgynous)
- Approximate age range
- Body type/build (slim, athletic, average, plus-size, etc.)
- Height perception (tall, average, short - based on proportions)
- Skin tone (fair, light, medium, tan, brown, deep, etc.)
- Hair color and style

PART 2 - Current Outfit (what they're wearing in the photo):
List each visible clothing item/accessory they're currently wearing:
- Top(s): shirts, jackets, etc.
- Bottom(s): pants, skirts, etc.
- Footwear: shoes, boots, etc.
- Accessories: hats, glasses, jewelry, bags, etc.

Format as two clear sections. Be concise but complete. Under 100 words total."""
                ),
            ],
        )
    ]

    # Configure for text-only response
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["TEXT"],
        temperature=0.3,
    )

    # Generate description
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=generate_content_config,
    )

    description = response.text.strip()
    return description


def describe_clothing_items(image_paths, api_key=None, rate_limit_delay=0.2, progress_callback=None):
    """
    Generate descriptions for multiple clothing items.

    Args:
        image_paths: List of paths to clothing images
        api_key: Google API key (optional)
        rate_limit_delay: Seconds to wait between API calls (default: 0.2)
        progress_callback: Optional callback function(idx, total, description)

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

            # Call progress callback if provided
            if progress_callback:
                progress_callback(idx, len(image_paths), description)

            # Rate limiting: wait between API calls to avoid hitting rate limits
            if idx < len(image_paths):  # Don't wait after the last item
                time.sleep(rate_limit_delay)

        except Exception as e:
            print(f"  ✗ Error describing image: {e}")

            # Check if it's a rate limit error
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str or "429" in error_str:
                print(f"  ⏳ Rate limit detected. Waiting 5 seconds before retry...")
                time.sleep(5)

                # Retry once
                try:
                    description = describe_clothing_item(image_path, api_key)
                    descriptions.append({
                        "index": idx,
                        "path": image_path,
                        "description": description
                    })
                    print(f"  → {description} (retry successful)")
                    time.sleep(rate_limit_delay)
                except Exception as retry_e:
                    print(f"  ✗ Retry failed: {retry_e}")
                    fallback_desc = f"clothing item from {os.path.basename(image_path)}"
                    descriptions.append({
                        "index": idx,
                        "path": image_path,
                        "description": fallback_desc
                    })
            else:
                # Use filename as fallback description for non-rate-limit errors
                fallback_desc = f"clothing item from {os.path.basename(image_path)}"
                descriptions.append({
                    "index": idx,
                    "path": image_path,
                    "description": fallback_desc
                })

    return descriptions
