"""
Gemini Image Generation Service

Generates outfit images using Google's Gemini NanoBanana model.
Based on outfit_image_gen.py with enhancements for the service layer.
"""

import os
import mimetypes
import asyncio
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
        try:
            print(f"  Loading image {idx}: {os.path.basename(image_path)}")
            image_bytes, mime_type = read_local_image(image_path)
            image_parts.append(
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            )
        except Exception as e:
            print(f"  ✗ Error loading image {idx}: {e}")
            # Continue with other images

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
    text_responses = []

    try:
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
                # Collect text responses for debugging
                if hasattr(chunk, 'text') and chunk.text:
                    text_responses.append(chunk.text)
                    print(chunk.text, end="", flush=True)

    except Exception as stream_error:
        print(f"\n  ⚠ Stream error: {stream_error}")
        # Continue to check if we got an image before the error

    print("\n")

    if generated_file_path:
        print(f"✓ Outfit image generated successfully!")
        return generated_file_path
    else:
        # Provide more detailed error information
        error_msg = "Failed to generate outfit image. No image returned by API."
        if text_responses:
            error_msg += f" Text response: {' '.join(text_responses)[:100]}"
        raise Exception(error_msg)


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


def generate_multiple_outfits(outfits, output_dir="output", api_key=None):
    """
    Generate multiple outfit images in parallel using async processing.

    Args:
        outfits: List of outfit dicts from gradient_agent.select_outfit()
        output_dir: Directory to save generated images
        api_key: Google API key (optional)

    Returns:
        list[dict]: Updated outfit dicts with "generated_image_path" added to each

    Example:
        outfits = [
            {"outfit_number": 1, "selected_paths": [...], "reasoning": "..."},
            {"outfit_number": 2, "selected_paths": [...], "reasoning": "..."}
        ]
        results = generate_multiple_outfits(outfits)
        # results[0]["generated_image_path"] = "output/outfit_1_20241213.jpg"
    """
    async def generate_single_async(outfit, outfit_num):
        """Async wrapper for single outfit generation with retry"""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"\n🔄 Retrying outfit {outfit_num} (attempt {attempt + 1}/{max_retries})...")
                else:
                    print(f"\n🎨 Generating outfit {outfit_num}/{len(outfits)}...")

                # Run synchronous generation in thread pool
                loop = asyncio.get_event_loop()
                image_path = await loop.run_in_executor(
                    None,
                    generate_outfit_image,
                    outfit["selected_paths"],
                    output_dir,
                    api_key
                )

                outfit["generated_image_path"] = image_path
                print(f"   ✓ Outfit {outfit_num} complete: {image_path}")
                return outfit

            except Exception as e:
                error_str = str(e)
                print(f"   ✗ Error generating outfit {outfit_num}: {error_str}")

                # Check if it's the last attempt
                if attempt == max_retries - 1:
                    outfit["generated_image_path"] = None
                    outfit["error"] = error_str
                    return outfit
                # No delay, continue immediately to next retry

        return outfit

    async def generate_all():
        """Generate all outfits in parallel"""
        tasks = [
            generate_single_async(outfit, outfit["outfit_number"])
            for outfit in outfits
        ]
        return await asyncio.gather(*tasks)

    # Run async generation
    print(f"\n🚀 Generating {len(outfits)} outfit image(s) in parallel...")
    results = asyncio.run(generate_all())

    return results
