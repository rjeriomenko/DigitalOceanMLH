#!/usr/bin/env python3
"""
Fashion AI - CLI Outfit Generator

A hackathon project that generates personalized outfit images using:
- Gemini Vision API for image understanding
- DigitalOcean Gradient Agent for fashion styling
- Gemini NanoBanana for image generation

Usage:
    python main.py <image1.jpg> <image2.jpg> ... [--selfie <selfie.jpg>]

Example:
    python main.py clothing/shirt.jpg clothing/pants.jpg clothing/jacket.jpg
    python main.py clothing/*.jpg --selfie selfies/me.jpg
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from services.utils import validate_image_paths, validate_image_path
from services.image_processor import describe_clothing_items, describe_person_appearance
from services.gradient_agent import select_outfit
from services.gemini_generator import generate_multiple_outfits


def print_banner():
    """Print a nice ASCII banner"""
    banner = """
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║              👔 FASHION AI OUTFIT GENERATOR 👗        ║
║                                                       ║
║         Powered by DigitalOcean Gradient AI          ║
║              & Google Gemini NanoBanana              ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)


def print_usage():
    """Print usage instructions"""
    print("\nUsage:")
    print("  python main.py <image1.jpg> <image2.jpg> ... [--selfie <selfie.jpg>]")
    print("\nExamples:")
    print("  python main.py clothing/shirt.jpg clothing/pants.jpg clothing/jacket.jpg")
    print("  python main.py clothing/*.jpg --selfie selfies/me.jpg")
    print("\nArguments:")
    print("  clothing images    1-20 images of clothing items")
    print("  --selfie IMAGE     (Optional) Your photo for personalized outfit generation")
    print("\nRequirements:")
    print("  - 1-20 clothing item images")
    print("  - Valid image formats: jpg, jpeg, png, gif, bmp, webp")
    print("  - API keys set in .env file:")
    print("    • GOOGLE_API_KEY")
    print("    • GRADIENT_AGENT_ACCESS_KEY")
    print("    • GRADIENT_AGENT_ENDPOINT")
    print()


def check_environment():
    """
    Check that required environment variables are set.

    Returns:
        bool: True if all required vars are set, False otherwise
    """
    required_vars = [
        "GOOGLE_API_KEY",
        "GRADIENT_AGENT_ACCESS_KEY",
        "GRADIENT_AGENT_ENDPOINT"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file.")
        print("See .env.example for reference.")
        return False

    return True


def main():
    """Main CLI orchestrator"""
    print_banner()

    # Check command line arguments
    if len(sys.argv) < 2:
        print("❌ Error: No images provided")
        print_usage()
        sys.exit(1)

    if sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0)

    # Parse command line arguments
    image_paths = []
    selfie_path = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--selfie':
            if i + 1 < len(args):
                selfie_path = args[i + 1]
                i += 2
            else:
                print("❌ Error: --selfie requires an image path")
                sys.exit(1)
        else:
            image_paths.append(args[i])
            i += 1

    print(f"📸 Received {len(image_paths)} clothing images")
    if selfie_path:
        print(f"🤳 Personalized mode: Using selfie from {selfie_path}")
    print("-" * 55)

    try:
        # Step 0: Check environment
        print("\n🔑 Checking environment variables...")
        if not check_environment():
            sys.exit(1)
        print("   ✓ All required API keys found")

        # Step 1: Validate images
        print("\n📋 Step 1: Validating images...")
        validate_image_paths(image_paths, max_count=20)
        print(f"   ✓ All {len(image_paths)} clothing images are valid")

        # Validate selfie if provided
        person_description = None
        if selfie_path:
            validate_image_path(selfie_path)
            print(f"   ✓ Selfie image is valid")

            # Describe the person
            print("\n👤 Step 1b: Analyzing your appearance...")
            person_description = describe_person_appearance(selfie_path)
            print(f"   Person: {person_description}")

        # Step 2: Generate semantic descriptions
        print("\n🔍 Step 2: Analyzing clothing items with Gemini Vision...")
        clothing_descriptions = describe_clothing_items(image_paths)
        print(f"   ✓ Generated descriptions for {len(clothing_descriptions)} items")

        # Step 3: Agent selects outfits (1-3 combinations)
        if person_description:
            print("\n👔 Step 3: Consulting DigitalOcean fashion agent for personalized outfit combinations...")
        else:
            print("\n👔 Step 3: Consulting DigitalOcean fashion agent for outfit combinations...")
        outfits = select_outfit(clothing_descriptions, person_description=person_description)

        print(f"   ✓ Agent created {len(outfits)} outfit(s)")
        for outfit in outfits:
            print(f"\n   Outfit {outfit['outfit_number']}:")
            print(f"      Items: {', '.join(map(str, outfit['selected_indices']))}")
            print(f"      Style: {outfit['reasoning'][:80]}...")
            print(f"      Wear: {outfit.get('wearing_instructions', 'N/A')[:60]}...")

        # Step 4: Generate outfit images in parallel
        if selfie_path:
            print(f"\n🎨 Step 4: Generating {len(outfits)} personalized outfit image(s) with Gemini NanoBanana...")
        else:
            print(f"\n🎨 Step 4: Generating {len(outfits)} outfit image(s) with Gemini NanoBanana...")
        results = generate_multiple_outfits(outfits, output_dir="output", selfie_path=selfie_path)

        # Success!
        print("\n" + "=" * 55)
        print(f"✅ SUCCESS! {len(results)} outfit image(s) generated!")
        print("=" * 55)

        # Display results
        for result in results:
            if result.get("generated_image_path"):
                print(f"\n📁 Outfit {result['outfit_number']}: {result['generated_image_path']}")
                print(f"   {result['reasoning'][:60]}...")
            elif result.get("error"):
                print(f"\n❌ Outfit {result['outfit_number']}: Generation failed - {result['error']}")

        print(f"\n💡 Tip: Check the output/ folder to see all {len(results)} AI-generated outfit(s)!")
        print()

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Please check that all image paths are correct.")
        return 1

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("\n🔍 Debug info:")
        print(f"   - Number of images: {len(image_paths)}")
        print(f"   - Image paths: {image_paths}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
