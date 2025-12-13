#!/usr/bin/env python3
"""
Fashion AI - Web Application
Flask server with WebSocket support for real-time progress updates
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import tempfile
import shutil
from pathlib import Path
import traceback

# Load environment variables
load_dotenv()

# Import our services
from services.utils import validate_image_path
from services.image_processor import describe_clothing_items, describe_person_appearance
from services.gradient_agent import select_outfit
from services.gemini_generator import generate_multiple_outfits
from services.query_handler import handle_query
from services.session_manager import get_session_manager
from services.image_converter import validate_and_prepare_image
from models.schemas import UploadedImage, GenerationProgress

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max (for multiple high-res images)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fashion-ai-secret-key-change-in-production')

# Enable CORS
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Get session manager
session_manager = get_session_manager()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'heic', 'heif'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def emit_progress(sid: str, step: str, message: str, percent: int, details: dict = None):
    """Emit progress update via WebSocket"""
    progress = GenerationProgress(
        step=step,
        message=message,
        progress_percent=percent,
        details=details or {}
    )
    socketio.emit('progress', progress.to_dict(), room=sid)


def get_weather_context():
    """
    Get current weather context for outfit recommendations.

    Returns:
        str: Weather context string to add to outfit selection instructions
    """
    try:
        import requests

        # Get client IP from Flask request context
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # Default weather context for localhost/private IPs
        if client_ip in ['127.0.0.1', 'localhost'] or client_ip.startswith('192.168.') or client_ip.startswith('10.'):
            return "WEATHER CONTEXT: Current conditions in New York - 72°F and clear/sunny. Consider weather-appropriate outfit choices."

        # Try to get real location and weather
        try:
            geo_response = requests.get(f'https://ipapi.co/{client_ip}/json/', timeout=2)
            if geo_response.ok:
                geo_data = geo_response.json()
                city = geo_data.get('city', 'your location')
                latitude = geo_data.get('latitude')
                longitude = geo_data.get('longitude')

                if latitude and longitude:
                    # Get weather from open-meteo
                    weather_response = requests.get(
                        f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,weather_code&temperature_unit=fahrenheit',
                        timeout=2
                    )

                    if weather_response.ok:
                        weather_data = weather_response.json()
                        current = weather_data.get('current', {})
                        temp = current.get('temperature_2m', 72)
                        weather_code = current.get('weather_code', 0)

                        # Map weather codes to descriptions
                        weather_map = {
                            0: 'clear/sunny', 1: 'mainly clear', 2: 'partly cloudy', 3: 'overcast',
                            45: 'foggy', 48: 'foggy', 51: 'light drizzle', 53: 'moderate drizzle',
                            55: 'dense drizzle', 61: 'slight rain', 63: 'moderate rain', 65: 'heavy rain',
                            71: 'slight snow', 73: 'moderate snow', 75: 'heavy snow', 80: 'rain showers',
                            81: 'rain showers', 82: 'heavy rain showers', 95: 'thunderstorm'
                        }
                        weather_desc = weather_map.get(weather_code, 'clear')

                        return f"WEATHER CONTEXT: Current conditions in {city} - {temp}°F and {weather_desc}. Consider weather-appropriate outfit choices."
        except:
            pass

        # Fallback
        return "WEATHER CONTEXT: Consider weather-appropriate outfit choices for current conditions."

    except Exception as e:
        print(f"Error getting weather context: {e}")
        return None


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate_outfits():
    """
    Main endpoint for outfit generation with progress updates

    Accepts:
        - clothing_images: List of clothing item images (required)
        - selfie: Optional selfie image
        - query: Optional text query (question or additional instructions)
        - session_id: Optional session ID for continued conversation

    Returns:
        JSON with outfits, query response, and session_id
    """
    # Get Socket.IO session ID from headers
    socket_sid = request.headers.get('X-Socket-ID', 'server')

    try:
        emit_progress(socket_sid, "starting", "Starting outfit generation...", 0)

        # Get optional query and session ID
        query = request.form.get('query', '').strip()
        session_id = request.form.get('session_id', '').strip()

        # Get precomputed descriptions if available
        precomputed_descriptions_json = request.form.get('precomputed_descriptions', '{}')
        try:
            precomputed_descriptions = json.loads(precomputed_descriptions_json)
        except:
            precomputed_descriptions = {}

        # Check if images or query were provided
        clothing_files = request.files.getlist('clothing_images') if 'clothing_images' in request.files else []

        # Allow text-only queries for conversation
        if not clothing_files and not query:
            emit_progress(socket_sid, "error", "Please provide clothing images or a question", 0)
            return jsonify({'error': 'Please provide clothing images or a question'}), 400

        # Get optional selfie
        selfie_file = request.files.get('selfie')

        # Get or create session
        session, is_new_session = session_manager.get_or_create_session(session_id if session_id else None)
        session_id = session.session_id

        emit_progress(
            socket_sid,
            "validating_images",
            f"Validating {len(clothing_files)} clothing images...",
            5,
            {"session_id": session_id, "is_new_session": is_new_session}
        )

        # Create temp directory for this request
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])

        try:
            # Handle text-only queries (no images)
            if not clothing_files and query:
                emit_progress(socket_sid, "consulting_agent", "Processing your question...", 50)

                # Add query to session history
                session.add_message("user", query)

                # Get text-only response from query handler
                query_result = handle_query(query, [], None)

                query_response = None
                if query_result['type'] == 'question':
                    query_response = query_result['answer']
                    session.add_message("assistant", query_response)

                emit_progress(socket_sid, "complete", "Response ready", 100)

                # Build response without outfits
                response_data = {
                    'success': True,
                    'session_id': session_id,
                    'is_new_session': is_new_session,
                    'conversation_context': session.get_context_summary(),
                    'query_response': query_response,
                    'outfits': []
                }

                return jsonify(response_data)

            # Save and validate clothing images
            clothing_images = []
            for idx, file in enumerate(clothing_files):
                if file and file.filename:
                    # Secure the filename (handles any crazy filenames)
                    original_name = secure_filename(file.filename) if file.filename else f"image_{idx}"
                    if not original_name or original_name == '':
                        original_name = f"clothing_{idx}.jpg"

                    # Save with safe name
                    safe_name = f"clothing_{idx}_{original_name}"
                    filepath = os.path.join(temp_dir, safe_name)
                    file.save(filepath)

                    # Validate and convert if needed
                    try:
                        processed_path, mime_type = validate_and_prepare_image(filepath)

                        clothing_images.append(UploadedImage(
                            original_filename=file.filename or safe_name,
                            saved_path=processed_path,
                            mime_type=mime_type,
                            file_size=os.path.getsize(processed_path),
                            image_type="clothing"
                        ))
                    except Exception as e:
                        print(f"Error processing image {idx}: {e}")
                        continue

            if not clothing_images:
                emit_progress(socket_sid, "error", "No valid clothing images", 0)
                return jsonify({'error': 'No valid clothing images provided'}), 400

            if len(clothing_images) > 20:
                emit_progress(socket_sid, "error", "Too many images (max 20)", 0)
                return jsonify({'error': f'Too many images. Maximum: 20, provided: {len(clothing_images)}'}), 400

            clothing_paths = [img.saved_path for img in clothing_images]

            # Save and validate selfie if provided
            selfie_image = None
            selfie_path = None
            person_description = None

            if selfie_file and selfie_file.filename:
                emit_progress(socket_sid, "analyzing_selfie", "Analyzing your selfie...", 15)

                original_name = secure_filename(selfie_file.filename) if selfie_file.filename else "selfie.jpg"
                if not original_name or original_name == '':
                    original_name = "selfie.jpg"

                filepath = os.path.join(temp_dir, f"selfie_{original_name}")
                selfie_file.save(filepath)

                try:
                    processed_path, mime_type = validate_and_prepare_image(filepath)

                    selfie_image = UploadedImage(
                        original_filename=selfie_file.filename or original_name,
                        saved_path=processed_path,
                        mime_type=mime_type,
                        file_size=os.path.getsize(processed_path),
                        image_type="selfie"
                    )
                    selfie_path = selfie_image.saved_path

                    # Describe the person
                    person_description = describe_person_appearance(selfie_path)

                    emit_progress(
                        socket_sid,
                        "analyzing_selfie",
                        "Selfie analyzed successfully",
                        20,
                        {"person_description": person_description[:100] + "..."}
                    )
                except Exception as e:
                    print(f"Error processing selfie: {e}")
                    # Continue without selfie

            # Describe clothing items with per-item progress
            # Use precomputed descriptions if available
            clothing_descriptions = []

            # Check if we have all precomputed descriptions
            all_precomputed = all(str(i) in precomputed_descriptions for i in range(len(clothing_paths)))

            if all_precomputed and len(precomputed_descriptions) > 0:
                # Use precomputed descriptions
                emit_progress(
                    socket_sid,
                    "analyzing_clothing",
                    f"Using cached descriptions for {len(clothing_paths)} items...",
                    25
                )

                for idx, path in enumerate(clothing_paths):
                    clothing_descriptions.append({
                        "index": idx + 1,
                        "path": path,
                        "description": precomputed_descriptions.get(str(idx), "clothing item")
                    })

                emit_progress(
                    socket_sid,
                    "analyzing_clothing",
                    f"Loaded {len(clothing_descriptions)} cached descriptions",
                    40,
                    {"items_count": len(clothing_descriptions)}
                )
            else:
                # Process normally with Vision API
                emit_progress(
                    socket_sid,
                    "analyzing_clothing",
                    f"Analyzing {len(clothing_paths)} clothing items with Gemini Vision...",
                    25
                )

                # Create progress callback for clothing analysis
                def clothing_progress_callback(idx, total, description):
                    # Calculate incremental progress between 25% and 40%
                    progress_percent = 25 + int((idx / total) * 15)
                    emit_progress(
                        socket_sid,
                        "analyzing_clothing",
                        f"Analyzed item {idx}/{total}: {description[:50]}...",
                        progress_percent,
                        {"current_item": idx, "total_items": total}
                    )

                clothing_descriptions = describe_clothing_items(
                    clothing_paths,
                    progress_callback=clothing_progress_callback
                )

                emit_progress(
                    socket_sid,
                    "analyzing_clothing",
                    f"Analyzed {len(clothing_descriptions)} items",
                    40,
                    {"items_count": len(clothing_descriptions)}
                )

            # Get weather context for outfit recommendations
            weather_context = get_weather_context()

            # Handle query if provided
            query_response = None
            additional_instructions = None

            if query:
                # Add query to session history
                session.add_message("user", query)

                emit_progress(socket_sid, "consulting_agent", "Processing your query...", 45)

                query_result = handle_query(
                    query,
                    clothing_descriptions,
                    person_description
                )

                if query_result['type'] == 'question':
                    query_response = query_result['answer']
                    session.add_message("assistant", query_response)
                elif query_result['type'] == 'instruction':
                    additional_instructions = query_result['instructions']

            # Add weather context to additional instructions
            if weather_context:
                if additional_instructions:
                    additional_instructions = f"{additional_instructions}\n\n{weather_context}"
                else:
                    additional_instructions = weather_context

            # Generate outfits with agent
            emit_progress(
                socket_sid,
                "consulting_agent",
                "Consulting DigitalOcean fashion agent for outfit combinations...",
                50
            )

            outfits = select_outfit(
                clothing_descriptions,
                person_description=person_description,
                additional_instructions=additional_instructions
            )

            emit_progress(
                socket_sid,
                "generating_images",
                f"Generating {len(outfits)} outfit image(s) with Gemini NanoBanana...",
                60,
                {"total_outfits": len(outfits)}
            )

            # Track completed outfits for progress (handles out-of-order completion)
            completed_outfits = {'count': 0}

            # Create progress callback for outfit generation with live preview
            def outfit_progress_callback(outfit_num, total, image_path):
                # Increment completed count
                completed_outfits['count'] += 1
                completed_count = completed_outfits['count']

                # Calculate incremental progress based on completed count (not outfit number)
                progress_percent = 60 + int((completed_count / total) * 35)

                # Emit progress update
                emit_progress(
                    socket_sid,
                    "generating_images",
                    f"Generated {completed_count}/{total} outfits",
                    progress_percent,
                    {"completed_outfits": completed_count, "total_outfits": total}
                )

                # Emit live preview event with the image URL
                image_filename = os.path.basename(image_path)
                image_url = f'/output/{image_filename}'
                socketio.emit('outfit_ready', {
                    'outfit_number': outfit_num,
                    'image_url': image_url,
                    'total_outfits': total
                }, room=socket_sid)

            # Generate outfit images
            results = generate_multiple_outfits(
                outfits,
                output_dir=app.config['OUTPUT_FOLDER'],
                selfie_path=selfie_path,
                progress_callback=outfit_progress_callback
            )

            emit_progress(socket_sid, "generating_images", "All images generated successfully", 95)

            # Build response
            response_data = {
                'success': True,
                'session_id': session_id,
                'is_new_session': is_new_session,
                'conversation_context': session.get_context_summary(),
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
                    image_filename = os.path.basename(result['generated_image_path'])
                    outfit_data['image_url'] = f'/output/{image_filename}'
                elif result.get('error'):
                    outfit_data['error'] = result['error']

                response_data['outfits'].append(outfit_data)

            emit_progress(
                socket_sid,
                "complete",
                f"Complete! Generated {len(results)} outfit(s)",
                100,
                {"outfits_count": len(results)}
            )

            return jsonify(response_data)

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except ValueError as e:
        emit_progress(socket_sid, "error", str(e), 0)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in generate_outfits: {e}")
        traceback.print_exc()
        emit_progress(socket_sid, "error", f"Server error: {str(e)}", 0)
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/output/<filename>')
def serve_output(filename):
    """Serve generated outfit images"""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/api/convert-heic', methods=['POST'])
def convert_heic():
    """
    Convert HEIC image to JPEG and return the converted image

    Accepts:
        - image: HEIC image file
        - filename: Original filename

    Returns:
        JPEG image blob
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['image']

        if not image_file or not image_file.filename:
            return jsonify({'error': 'Invalid image'}), 400

        # Create temp directory
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])

        try:
            # Save file
            safe_name = secure_filename(image_file.filename) if image_file.filename else 'temp.heic'
            filepath = os.path.join(temp_dir, safe_name)
            image_file.save(filepath)

            # Validate and convert if needed (this handles HEIC conversion with pillow-heif)
            processed_path, mime_type = validate_and_prepare_image(filepath)

            # Return the converted image as a blob
            return send_from_directory(os.path.dirname(processed_path), os.path.basename(processed_path), mimetype='image/jpeg')

        finally:
            # Clean up temp directory after a delay
            import threading
            def cleanup():
                import time
                time.sleep(5)  # Wait 5 seconds for response to be sent
                shutil.rmtree(temp_dir, ignore_errors=True)
            threading.Thread(target=cleanup).start()

    except Exception as e:
        print(f"Error converting HEIC: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Conversion error: {str(e)}'}), 500


@app.route('/api/describe-image', methods=['POST'])
def describe_image():
    """
    Pre-process a single clothing image with Gemini Vision.

    Accepts:
        - image: Single image file
        - filename: Original filename for de-duplication

    Returns:
        JSON with description or error
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400

        image_file = request.files['image']
        filename = request.form.get('filename', image_file.filename)

        if not image_file or not image_file.filename:
            return jsonify({'error': 'Invalid image'}), 400

        # Create temp directory for this image
        temp_dir = tempfile.mkdtemp(dir=app.config['UPLOAD_FOLDER'])

        try:
            # Save and validate image
            safe_name = secure_filename(filename) if filename else 'temp.jpg'
            filepath = os.path.join(temp_dir, safe_name)
            image_file.save(filepath)

            # Validate and convert if needed
            processed_path, mime_type = validate_and_prepare_image(filepath)

            # Describe the image
            description = describe_clothing_items(
                [processed_path],
                progress_callback=None
            )

            if description and len(description) > 0:
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'description': description[0]['description']
                })
            else:
                return jsonify({'error': 'Failed to describe image'}), 500

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"Error in describe_image: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_info(session_id):
    """Get information about a session"""
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404

    return jsonify({
        'session_id': session.session_id,
        'message_count': len(session.messages),
        'created_at': session.created_at.isoformat(),
        'last_updated': session.last_updated.isoformat(),
        'context': session.get_context_summary()
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'active_sessions': session_manager.get_session_count()
    })


@app.route('/api/location-weather', methods=['GET'])
def get_location_weather():
    """
    Get user's location and weather from IP address

    Returns:
        JSON with location, weather, and suggested background prompt
    """
    try:
        # Get client IP (handle proxies)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        # For localhost/private IPs, use a default location
        if client_ip in ['127.0.0.1', 'localhost'] or client_ip.startswith('192.168.') or client_ip.startswith('10.'):
            return jsonify({
                'location': 'New York',
                'country': 'United States',
                'weather': 'sunny',
                'temperature': 72,
                'description': 'Clear sky',
                'is_fallback': True
            })

        # Use ipapi.co for geolocation (free, no API key needed)
        import requests

        geo_response = requests.get(f'https://ipapi.co/{client_ip}/json/', timeout=3)
        geo_data = geo_response.json()

        city = geo_data.get('city', 'New York')
        country = geo_data.get('country_name', 'United States')
        lat = geo_data.get('latitude')
        lon = geo_data.get('longitude')

        # Get weather from open-meteo.com (free, no API key needed)
        weather_response = requests.get(
            f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&temperature_unit=fahrenheit',
            timeout=3
        )
        weather_data = weather_response.json()

        # Map weather codes to simple descriptions
        weather_code = weather_data.get('current', {}).get('weather_code', 0)
        weather_map = {
            0: 'sunny', 1: 'partly cloudy', 2: 'cloudy', 3: 'cloudy',
            45: 'foggy', 48: 'foggy',
            51: 'rainy', 53: 'rainy', 55: 'rainy', 56: 'rainy', 57: 'rainy',
            61: 'rainy', 63: 'rainy', 65: 'rainy', 66: 'rainy', 67: 'rainy',
            71: 'snowy', 73: 'snowy', 75: 'snowy', 77: 'snowy',
            80: 'rainy', 81: 'rainy', 82: 'rainy',
            85: 'snowy', 86: 'snowy',
            95: 'stormy', 96: 'stormy', 99: 'stormy'
        }

        weather = weather_map.get(weather_code, 'sunny')
        temperature = weather_data.get('current', {}).get('temperature_2m', 72)

        return jsonify({
            'location': city,
            'country': country,
            'weather': weather,
            'temperature': int(temperature),
            'description': weather.capitalize(),
            'is_fallback': False
        })

    except Exception as e:
        print(f"Error getting location/weather: {e}")
        # Fallback to New York on sunny day
        return jsonify({
            'location': 'New York',
            'country': 'United States',
            'weather': 'sunny',
            'temperature': 72,
            'description': 'Clear sky',
            'is_fallback': True
        })


@app.route('/api/generate-background', methods=['POST'])
def generate_background():
    """
    Generate a background image using Gemini NanoBanana

    Accepts:
        - location: City name
        - weather: Weather condition (sunny/cloudy/rainy/snowy)

    Returns:
        JSON with background image path
    """
    try:
        data = request.get_json()
        location = data.get('location', 'New York')
        weather = data.get('weather', 'sunny')

        # Import Gemini generator
        from services.gemini_generator import generate_outfit_image_simple

        # Create a descriptive prompt for the background
        prompt = f"A beautiful, atmospheric photograph of {location} on a {weather} day. Professional travel photography style, vibrant colors, high quality, wide angle cityscape or landmark view. {weather} weather clearly visible. Photorealistic, 8K quality."

        # Generate the image
        output_dir = app.config['OUTPUT_FOLDER']
        os.makedirs(output_dir, exist_ok=True)

        # Generate background image (use simple version, no outfit needed)
        generated_image_path = generate_outfit_image_simple(
            image_paths=[],
            prompt=prompt,
            output_dir=output_dir
        )

        if generated_image_path:
            image_filename = os.path.basename(generated_image_path)
            return jsonify({
                'success': True,
                'image_url': f'/output/{image_filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to generate background image'}), 500

    except Exception as e:
        print(f"Error generating background: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")


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
    print("🚀 Starting Fashion AI Web Server with WebSocket support...")
    print(f"📱 Open http://localhost:{port} in your browser")

    # Run with SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
