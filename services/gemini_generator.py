"""
Gemini Image Generation Service

Generates outfit images using Google's Gemini NanoBanana model.
Based on outfit_image_gen.py with enhancements for the service layer.
"""

import os
import mimetypes
from datetime import datetime
from google import genai
from google.genai import types
from .utils import read_local_image, save_binary_file


def generate_outfit_image(selected_image_paths, output_dir="output", api_key=None):
    """
    Generate an outfit image using Gemini's image generation capabilities.

    Args:
        selected_image_paths: List of paths to selected clothing images
        output_dir: Directory to save generated images (default: "output")
        api_key: Google API key (optional, reads from env)

    Returns:
        str: Path to the generated image file

    Raises:
        ValueError: If no images provided or API key missing
        Exception: If image generation fails
    """
    if not selected_image_paths:
        raise ValueError("No clothing images provided for outfit generation")

    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nGenerating outfit image from {len(selected_image_paths)} clothing items...")

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    model = "gemini-3-pro-image-preview"

    # Read all selected images
    image_parts = []
    for idx, image_path in enumerate(selected_image_paths, start=1):
        print(f"  Loading image {idx}: {os.path.basename(image_path)}")
        image_bytes, mime_type = read_local_image(image_path)
        image_parts.append(
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        )

    # Create the prompt
    prompt = """You are given images of articles of clothing. Please generate a high-quality, realistic fashion photograph showing a model wearing EXACTLY these clothing items and NOTHING ELSE.

Requirements:
- Show ONLY the clothing items provided in the images
- Create a professional fashion photo style
- Use appropriate lighting and composition
- The model should be a realistic person in a neutral pose
- Ensure all clothing items are clearly visible and well-coordinated

Do not add any additional clothing, accessories, or items not shown in the input images."""

    # Add text prompt to parts
    image_parts.append(types.Part.from_text(text=prompt))

    # Create content
    contents = [
        types.Content(
            role="user",
            parts=image_parts,
        )
    ]

    # Configure generation
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(
            image_size="1K",  # 1024x1024 resolution
        ),
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
    )

    print("\nGenerating outfit image with Gemini NanoBanana...")

    # Generate image
    generated_file_path = None
    file_index = 0

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or not chunk.candidates
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue

        part = chunk.candidates[0].content.parts[0]

        # Check if the response part is an image
        if part.inline_data and part.inline_data.data:
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"outfit_{timestamp}_{file_index}"
            file_index += 1

            inline_data = part.inline_data
            data_buffer = inline_data.data

            # Guess file extension from MIME type
            file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"

            # Save to output directory
            full_path = os.path.join(output_dir, f"{file_name}{file_extension}")
            generated_file_path = save_binary_file(full_path, data_buffer)

        else:
            # Print any text response
            if hasattr(chunk, 'text') and chunk.text:
                print(chunk.text, end="", flush=True)

    print("\n")

    if generated_file_path:
        print(f"✓ Outfit image generated successfully!")
        return generated_file_path
    else:
        raise Exception("Failed to generate outfit image. No image returned by API.")


def generate_outfit_image_simple(image_paths, prompt, output_dir="output", api_key=None):
    """
    Simplified version for direct image generation with custom prompt.

    Args:
        image_paths: List of image paths
        prompt: Custom text prompt
        output_dir: Output directory
        api_key: Google API key (optional)

    Returns:
        str: Path to generated image
    """
    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")

    os.makedirs(output_dir, exist_ok=True)

    client = genai.Client(api_key=api_key)
    model = "gemini-3-pro-image-preview"

    # Read images
    image_list = [read_local_image(x) for x in image_paths]
    parts = [
        types.Part.from_bytes(data=x[0], mime_type=x[1])
        for x in image_list
    ]
    parts.append(types.Part.from_text(text=prompt))

    contents = [types.Content(role="user", parts=parts)]

    generate_content_config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        image_config=types.ImageConfig(image_size="1K"),
        tools=[types.Tool(googleSearch=types.GoogleSearch())],
    )

    generated_path = None
    file_index = 0

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates
            and chunk.candidates[0].content
            and chunk.candidates[0].content.parts
        ):
            part = chunk.candidates[0].content.parts[0]

            if part.inline_data and part.inline_data.data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"outfit_{timestamp}_{file_index}"
                file_index += 1

                file_extension = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                full_path = os.path.join(output_dir, f"{file_name}{file_extension}")
                generated_path = save_binary_file(full_path, part.inline_data.data)

    return generated_path
