# DebonAIr - Fashion AI Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  Weather Display • Carousel Background • Chat • Image Upload    │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket + REST API
┌────────────────────────────▼────────────────────────────────────┐
│                       FLASK BACKEND                              │
│  Session Manager • Query Handler • Image Processor • Weather    │
└────┬────────────────────┬─────────────────────┬─────────────────┘
     │                    │                     │
     ▼                    ▼                     ▼
┌─────────────┐  ┌──────────────────┐  ┌──────────────┐
│   Gemini    │  │  Gradient AI     │  │   Gemini     │
│   Vision    │  │  llama3.3-70b    │  │  NanoBanana  │
│  (Analyze)  │  │ (Fashion Expert) │  │  (Generate)  │
└─────────────┘  └──────────────────┘  └──────────────┘
```

## Data Flow

```
1. USER UPLOAD
   ├─ Selfies (0-3)
   ├─ Clothing (0-30)
   └─ Text Query
          ↓
2. GEMINI VISION ANALYSIS
   ├─ Person Description
   └─ Clothing Descriptions
          ↓
3. GRADIENT AI SELECTION
   ├─ Weather Context Added
   └─ Picks 1-12 Outfit Combinations
          ↓
4. GEMINI IMAGE GENERATION
   └─ Creates Virtual Try-On Images
          ↓
5. REAL-TIME DELIVERY
   └─ Socket.IO Stream to User
```

## Key Components

### Frontend (JavaScript)
- Real-time WebSocket updates
- Drag & drop image upload
- HEIC to JPEG conversion
- Sliding carousel background
- Image magnification on click

### Backend (Flask)
- Session management (60min)
- Intent detection (question vs instruction)
- Image processing & validation
- Weather API integration

### AI Models
- **Gradient AI (DigitalOcean)**: Fashion expert agent with llama3.3-70b
- **Gemini Vision**: Analyzes selfies and clothing items
- **Gemini NanoBanana**: Generates outfit visualization images

### External APIs
- Open-Meteo: Weather data
- ipapi.co: Geolocation
- Unsplash: Background images

## Features

**Smart Styling**
- Mix selfie items with wardrobe
- Color coordination
- Weather-appropriate recommendations
- Body type consideration

**Conversational AI**
- 60-minute session memory
- Question answering
- Style guidance
- Context-aware responses

**Visual Experience**
- Click to magnify outfits
- Sliding background carousel
- Real-time progress tracking
- Responsive design

**Demo Mode**
- Default wardrobe (30 items)
- Drag & drop upload
- HEIC auto-conversion

## Tech Stack

- Frontend: Vanilla JavaScript, HTML5/CSS3, Socket.IO
- Backend: Flask 3.0, Flask-SocketIO, Python 3.11+
- AI: DigitalOcean Gradient AI, Google Gemini 2.0
- APIs: Open-Meteo, ipapi.co, Unsplash
