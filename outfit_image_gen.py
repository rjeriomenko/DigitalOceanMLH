# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import mimetypes
import os
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")


def read_local_image(image_path):
    """Reads a local image file and returns the bytes and mime type."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Could not find image at: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # Default fallback

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    return image_bytes, mime_type


def generate(images, text_prompt):
    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY")
    )

    # Note: Ensure the model you select supports multimodal inputs (text + image)
    model = "gemini-3-pro-image-preview"

    # 1. Read the local image
    list = [read_local_image(x) for x in images]
    parts = [types.Part.from_bytes(
        data=x[0],
        mime_type=x[1]
    ) for x in list]
    parts.append(
        types.Part.from_text(text=text_prompt),
    )
    contents = [
        types.Content(
            role="user",
            parts=parts,
        ),
    ]

    tools = [
        types.Tool(googleSearch=types.GoogleSearch()),
    ]

    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",  # Note: Requesting image output
            "TEXT",
        ],
        image_config=types.ImageConfig(
            image_size="1K",
        ),
        tools=tools,
    )

    print(f"Generating based on images and prompt: '{text_prompt}'...")

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

        # Check if the response part is an image (Inline Data)
        if part.inline_data and part.inline_data.data:
            file_name = f"NanoBanana_Output_{file_index}"
            file_index += 1
            inline_data = part.inline_data
            data_buffer = inline_data.data

            # Use mimetypes to guess extension, default to .png if unknown
            file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"

            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            # Print text response
            print(chunk.text, end="", flush=True)

    print("\nDone.")


if __name__ == "__main__":
    # REPLACE THIS with the path to your local image

    # Prompt instructing the model what to do with the input image
    PROMPT = '''You are given images of articles of clothing along with a picture of myself. Please generate an image of me wearing the articles of clothing provided, and nothing else but the clothing that I have given you in this prompt.'''

    # Simple check to prevent errors if you run it without adding an image
    paths = [f"clothing/{x}.jpg" for x in range(1,6)]
    generate(paths, PROMPT)
