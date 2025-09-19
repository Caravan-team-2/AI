## Caravanes FastAPI

### Quickstart

1. Create and activate a virtualenv
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create a .env file with your configuration
```bash
# Database
DATABASE_URL=sqlite:///./caravanes.db

# Gemini API (required for OCR functionality)
GEMINI_API_KEY=your_gemini_api_key_here

# App Configuration
APP_NAME=Caravanes API
ENVIRONMENT=development
DEBUG=true
```

4. Run the API
```bash
uvicorn app.main:app --reload
```

### API Endpoints

- `GET /health`: Health check endpoint
- `POST /ocr/extract`: Extract data from Arabic license card images using Google Gemini Vision API
- `POST /damage/search-part-prices`: Deep search for damaged car part prices from single image
- `POST /damage/search-multi-angle-prices`: Deep search for damaged part prices from 4 angles (front, back, left, right)
- `POST /damage/search-custom-angle-prices`: Deep search for damaged part prices from custom angles
- `POST /license/detect`: Detect license IDs in uploaded image using trained YOLO model
- `POST /license/detect-batch`: Detect license IDs in multiple images (batch processing)
- `POST /license/crop-licenses`: Crop detected license IDs from image with confidence filtering
- `GET /license/model-info`: Get license detection model information

### Structure
- `app/main.py`: application factory and middleware
- `app/api/`: API routers (`health`, `ocr`, `damage`, `license`)
- `app/core/`: settings and configuration
- `app/db/`: SQLAlchemy engine/session/base
- `app/models/`: SQLAlchemy models
- `app/schema/`: Pydantic schemas
- `datasets/license_id/`: YOLO training dataset and scripts

### OCR Functionality

The OCR endpoint uses Google Gemini Vision API to extract:
- License number
- First name
- Last name

From Arabic license card images. Make sure to set your `GEMINI_API_KEY` in the `.env` file.

### Deep Price Search Functionality

The damage estimation endpoints use Google Gemini Vision API + real-time web search to find actual prices for damaged car parts:

**Single Image Price Search:**
- `POST /damage/search-part-prices`: Deep search for damaged part prices from one image
  - Identifies damaged parts using AI
  - Searches real-time prices from multiple sources
  - Returns detailed price information for each part

**Multi-Angle Price Search:**
- `POST /damage/search-multi-angle-prices`: Deep search from 4 angles
  - Requires 4 images: front, back, left, right views
  - Identifies all damaged parts across all angles
  - Searches prices for each damaged part
  - Provides comprehensive cost estimation

- `POST /damage/search-custom-angle-prices`: Flexible multi-angle price search
  - Upload any number of images with custom angle specifications
  - Comma-separated angle list (e.g., "front,left,back,top")
  - Searches prices for all identified damaged parts

**Key Features:**
- **AI Part Identification**: Uses Gemini Vision to identify specific damaged parts
- **Real-Time Price Search**: Searches multiple automotive parts websites
- **Price Aggregation**: Finds min, max, and average prices for each part
- **Car-Specific Results**: Includes car make, model, and year for accurate pricing
- **Multi-Source Search**: Searches Autoparts.com, RockAuto, PartsGeek, Amazon, etc.
- **Comprehensive Costing**: Total cost estimates across all damaged parts
- **Angle-Specific Tracking**: Shows which angle each damaged part was observed from

**Price Search Sources:**
- Autoparts.com
- RockAuto.com
- PartsGeek.com
- Amazon.com
- Google Shopping results

All endpoints return structured JSON responses with real-time price data for damaged car parts.

### License ID Detection Functionality

The license detection endpoints use trained YOLO models to detect and extract license IDs from images:

**Single Image Detection:**
- `POST /license/detect`: Detect license IDs in uploaded image
  - Returns bounding box coordinates
  - Provides confidence scores
  - Supports multiple license ID detection

**Batch Processing:**
- `POST /license/detect-batch`: Process multiple images at once
  - Maximum 10 images per batch
  - Returns results for each image
  - Efficient batch processing

**License Cropping:**
- `POST /license/crop-licenses`: Crop detected license IDs
  - Returns cropped license ID images as base64
  - Configurable confidence threshold
  - Filters low-confidence detections

**Model Information:**
- `GET /license/model-info`: Get model details
  - Model type and version
  - Classes and confidence threshold
  - Model performance metrics

**YOLO Training:**
- Complete YOLO training setup in `datasets/license_id/`
- Training scripts and validation tools
- Export functionality for different formats
- Comprehensive documentation

**Key Features:**
- **AI-Powered Detection**: Uses trained YOLO model for accurate detection
- **Multiple Formats**: Supports various image formats
- **Confidence Filtering**: Filter results by confidence threshold
- **Batch Processing**: Process multiple images efficiently
- **Cropping**: Extract individual license IDs from images
- **Real-time**: Fast inference with optimized models

**Training Your Own Model:**
1. Add images to `datasets/license_id/images/train/` and `datasets/license_id/images/val/`
2. Create corresponding label files in `datasets/license_id/labels/train/` and `datasets/license_id/labels/val/`
3. Run training: `cd datasets/license_id && python train_yolo.py`
4. Export model: `python export_and_test_yolo.py`
