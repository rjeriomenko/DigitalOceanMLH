#!/usr/bin/env python3
"""
Fashion AI - Web Application
Flask server for the Fashion AI outfit generator
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import tempfile
import shutil
from pathlib import Path

# Load environment variables
load_dotenv()

# Import our services
from services.utils import validate_image_paths, validate_image_path
from services.image_processor import describe_clothing_items, describe_person_appearance
from services.gradient_agent import select_outfit
from services.gemini_generator import generate_multiple_outfits
from services.query_handler import handle_query

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate_outfits():
    """
    Main endpoint for outfit generation

    Accepts:
        - clothing_images: List of clothing item images (required)
        - selfie: Optional selfie image
        - query: Optional text query (question or additional instructions)

    Returns:
        JSON with outfits and/or query response
    """
    try:
        # Check if images were provided
        if 'clothing_images' not in request.files:
            return jsonify({'error': 'No clothing images provided'}), 400

        clothing_files = request.files.getlist('clothing_images')
        if not clothing_files or len(clothing_files) == 0:
            return jsonify({'error': 'No clothing images provided'}), 400

        # Get optional selfie
        selfie_file = request.files.get('selfie')

        # Get optional query
        query = request.form.get('query', '').strip()

        # Create temp directory for this request
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])

        try:
            # Save clothing images
            clothing_paths = []
            for idx, file in enumerate(clothing_files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"clothing_{idx}_{file.filename}")
                    filepath = os.path.join(temp_dir, filename)
                    file.save(filepath)
                    clothing_paths.append(filepath)

            if not clothing_paths:
                return jsonify({'error': 'No valid clothing images provided'}), 400

            # Validate clothing images
            validate_image_paths(clothing_paths, max_count=20)

            # Save selfie if provided
            selfie_path = None
            person_description = None
            if selfie_file and allowed_file(selfie_file.filename):
                filename = secure_filename(f"selfie_{selfie_file.filename}")
                selfie_path = os.path.join(temp_dir, filename)
                selfie_file.save(selfie_path)
                validate_image_path(selfie_path)

                # Describe the person
                person_description = describe_person_appearance(selfie_path)

            # Describe clothing items
            clothing_descriptions = describe_clothing_items(clothing_paths)

            # Handle query if provided
            query_response = None
            additional_instructions = None
            if query:
                query_result = handle_query(
                    query,
                    clothing_descriptions,
                    person_description
                )

                if query_result['type'] == 'question':
                    query_response = query_result['answer']
                elif query_result['type'] == 'instruction':
                    additional_instructions = query_result['instructions']

            # Generate outfits
            outfits = select_outfit(
                clothing_descriptions,
                person_description=person_description,
                additional_instructions=additional_instructions
            )

            # Generate outfit images
            results = generate_multiple_outfits(
                outfits,
                output_dir=app.config['OUTPUT_FOLDER'],
                selfie_path=selfie_path
            )

            # Build response
            response_data = {
                'success': True,
                'outfits': []
            }

            if query_response:
                response_data['query_response'] = query_response

            for result in results:
                outfit_data = {
                    'outfit_number': result['outfit_number'],
                    'reasoning': result['reasoning'],
                    'wearing_instructions': result.get('wearing_instructions', 'N/A')
                }

                if result.get('generated_image_path'):
                    # Convert to relative path for URL
                    image_filename = os.path.basename(result['generated_image_path'])
                    outfit_data['image_url'] = f'/output/{image_filename}'
                elif result.get('error'):
                    outfit_data['error'] = result['error']

                response_data['outfits'].append(outfit_data)

            return jsonify(response_data)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in generate_outfits: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/output/<filename>')
def serve_output(filename):
    """Serve generated outfit images"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # Check environment variables
    required_vars = [
        "GOOGLE_API_KEY",
        "GRADIENT_AGENT_ACCESS_KEY",
        "GRADIENT_AGENT_ENDPOINT"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file.")
        exit(1)

    port = int(os.getenv('PORT', 5001))
    print("🚀 Starting Fashion AI Web Server...")
    print(f"📱 Open http://localhost:{port} in your browser")
    app.run(debug=True, host='0.0.0.0', port=port)
