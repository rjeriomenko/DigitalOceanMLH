# Fashion AI - Web Application

A beautiful, mobile-responsive web interface for the Fashion AI outfit generator.

## Features

- 🎨 **Clean, Modern UI** - Cute gradient design with smooth animations
- 📱 **Mobile Responsive** - Works perfectly on phones, tablets, and desktops
- 💬 **Query Support** - Ask questions or add styling instructions
- 🤳 **Optional Selfie** - Upload your photo for personalized outfit recommendations
- 👕 **Multi-Image Upload** - Upload 1-20 clothing items with live previews
- ✨ **Real-time Generation** - See your AI-generated outfits instantly
- 🎯 **Smart Query Handling** - AI determines if your query is a question or styling instruction

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Make sure your `.env` file has:

```bash
GOOGLE_API_KEY=your_google_api_key
GRADIENT_AGENT_ACCESS_KEY=your_gradient_key
GRADIENT_AGENT_ENDPOINT=your_gradient_endpoint
```

### 3. Run the Web Server

```bash
python app.py
```

### 4. Open in Browser

Navigate to: **http://localhost:5000**

## How to Use

### Basic Usage (Outfits Only)

1. Upload 1-20 clothing item images
2. Click "✨ Generate Outfits"
3. View your AI-generated outfit images!

### With Selfie (Personalized)

1. Upload your selfie (optional)
2. Upload clothing items
3. Click generate
4. Get personalized outfits styled specifically for you!

### With Query (Questions or Instructions)

**Ask a Question:**
```
"What would look good for a casual date?"
"Can I wear this to work?"
```

**Add Instructions:**
```
"Make the outfits more formal"
"I want colorful, fun outfits"
"Focus on streetwear style"
```

The AI will:
- Answer questions directly
- Apply instructions to outfit generation
- Or do both!

## API Endpoint

### POST `/api/generate`

**Request (multipart/form-data):**
- `clothing_images`: List of image files (required, 1-20 items)
- `selfie`: Single image file (optional)
- `query`: Text string (optional)

**Response (JSON):**
```json
{
  "success": true,
  "query_response": "Based on your wardrobe...", // if query was a question
  "outfits": [
    {
      "outfit_number": 1,
      "reasoning": "A sleek monochrome look...",
      "wearing_instructions": "Blazer buttoned, shirt tucked in...",
      "image_url": "/output/outfit_1_20241213_123456.jpg"
    }
  ]
}
```

## Tech Stack

**Backend:**
- Flask - Web framework
- DigitalOcean Gradient AI - Fashion styling agent
- Google Gemini Vision - Image understanding
- Google Gemini NanoBanana - Image generation

**Frontend:**
- Vanilla JavaScript - No frameworks needed!
- Modern CSS - Gradients, animations, responsive grid
- Fetch API - Async file uploads

## Project Structure

```
├── app.py                      # Flask web server
├── templates/
│   └── index.html             # Frontend UI
├── static/
│   ├── css/
│   │   └── style.css          # Styles & responsive design
│   └── js/
│       └── app.js             # Frontend logic
├── services/
│   ├── query_handler.py       # Query classification (question vs instruction)
│   ├── image_processor.py     # Gemini Vision API
│   ├── gradient_agent.py      # DigitalOcean agent
│   └── gemini_generator.py    # NanoBanana image generation
├── uploads/                    # Temporary upload storage
└── output/                     # Generated outfit images
```

## Deployment

### Local Development

Already done! Running `python app.py` starts the server on `http://localhost:5000`

### Vercel Deployment (Optional)

1. Install Vercel CLI:
```bash
npm install -g vercel
```

2. Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

3. Deploy:
```bash
vercel
```

**Note:** You'll need to add environment variables in Vercel dashboard.

### Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=app.py
EXPOSE 5000

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t fashion-ai .
docker run -p 5000:5000 --env-file .env fashion-ai
```

## Features in Detail

### Query Handler (`services/query_handler.py`)

Uses DigitalOcean's agent to intelligently classify user queries:

- **Questions**: Get immediate answers about styling, occasions, or outfit suitability
- **Instructions**: Additional styling guidance passed to outfit generator
- **Automatic Detection**: AI determines query type automatically

### Responsive Design

The UI adapts beautifully across devices:

- **Desktop**: Full-width preview grid, large buttons
- **Tablet**: Optimized touch targets, adjusted spacing
- **Mobile**: Single-column layout, bottom-aligned controls

### Image Preview

Live previews for all uploaded images with:
- Thumbnail grid display
- Remove buttons (× on each image)
- File count indicators
- Drag-and-drop support (browser default)

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or run on different port
python app.py  # Edit app.py to change port
```

### Missing Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables Not Found

Check that `.env` file exists and has all required keys.

## Development

### Adding New Features

The modular structure makes it easy to extend:

- **New endpoints**: Add to `app.py`
- **New AI services**: Create in `services/`
- **UI changes**: Edit `templates/index.html` or `static/`

### Testing API Directly

```bash
curl -X POST http://localhost:5000/api/generate \
  -F "clothing_images=@clothing/shirt.jpg" \
  -F "clothing_images=@clothing/pants.jpg" \
  -F "query=Make it formal"
```

## Credits

Built with ❤️ for DigitalOcean MLH Hackathon

Powered by:
- DigitalOcean Gradient AI Platform
- Google Gemini (Vision & NanoBanana)
