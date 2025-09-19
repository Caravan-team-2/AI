from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from typing import Dict, Any, List, Optional
from PIL import Image
import cv2
import numpy as np
import io
import os
import easyocr
from ultralytics import YOLO
import torch

router = APIRouter()

# Global variables for model caching
_yolo_model = None
_ocr_reader = None
def _get_yolo_model():
    """Get or initialize YOLO model for license plate detection"""
    global _yolo_model
    if _yolo_model is None:
        try:
            # Try to load from pre-downloaded model first
            model_path = os.path.join('/app/models', 'yolov8n.pt')
            if os.path.exists(model_path):
                _yolo_model = YOLO(model_path)
                print("YOLO model loaded from pre-downloaded file")
            else:
                # Fallback: download model (this will work if we have write permissions)
                _yolo_model = YOLO('yolov8n.pt')
                print("YOLO model downloaded and loaded")
        except Exception as e:
            print(f"Failed to load YOLO model: {e}")
            raise Exception(f"Could not load YOLO model: {str(e)}")
    return _yolo_model

def _get_ocr_reader():
    """Get or initialize EasyOCR reader"""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            # Set environment variables for EasyOCR
            os.environ['HOME'] = '/app'
            os.environ['EASYOCR_HOME'] = '/app/cache'
            
            # Initialize EasyOCR with English and Arabic support
            # Always use CPU in Docker for better compatibility
            _ocr_reader = easyocr.Reader(['en', 'ar'], gpu=False)
            print("EasyOCR reader initialized (CPU mode)")
        except Exception as e:
            print(f"Failed to initialize EasyOCR: {e}")
            # Try with minimal configuration
            try:
                _ocr_reader = easyocr.Reader(['en'], gpu=False)
                print("EasyOCR reader initialized with English only")
            except Exception as e2:
                print(f"EasyOCR initialization completely failed: {e2}")
                # Try with even more minimal setup
                try:
                    import tempfile
                    with tempfile.TemporaryDirectory() as temp_dir:
                        os.environ['HOME'] = temp_dir
                        _ocr_reader = easyocr.Reader(['en'], gpu=False)
                        print("EasyOCR reader initialized with temporary directory")
                except Exception as e3:
                    print(f"All EasyOCR initialization attempts failed: {e3}")
                    raise e3
    return _ocr_reader

def _detect_license_plates_yolo(image: np.ndarray) -> List[Dict[str, Any]]:
    """Detect license plates using YOLO model"""
    model = _get_yolo_model()
    
    # Run YOLO inference
    results = model(image, conf=0.5)  # confidence threshold
    
    license_plates = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                # Get class name
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                
                # Filter for objects that might be license plates
                # YOLO doesn't have a specific license plate class, so we'll look for:
                # - cars (class 2) and extract regions that might contain license plates
                # - or use a more general approach
                if class_name in ['car', 'truck', 'bus', 'motorcycle'] and confidence > 0.6:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Extract the region that might contain license plate
                    # License plates are typically in the lower portion of vehicles
                    height = y2 - y1
                    width = x2 - x1
                    
                    # Focus on lower 30% of the vehicle for license plate detection
                    license_plate_y1 = int(y1 + height * 0.7)
                    license_plate_y2 = int(y2)
                    license_plate_x1 = int(x1)
                    license_plate_x2 = int(x2)
                    
                    # Ensure coordinates are within image bounds
                    license_plate_y1 = max(0, license_plate_y1)
                    license_plate_y2 = min(image.shape[0], license_plate_y2)
                    license_plate_x1 = max(0, license_plate_x1)
                    license_plate_x2 = min(image.shape[1], license_plate_x2)
                    
                    if license_plate_y2 > license_plate_y1 and license_plate_x2 > license_plate_x1:
                        license_plates.append({
                            'bbox': [license_plate_x1, license_plate_y1, license_plate_x2, license_plate_y2],
                            'confidence': confidence,
                            'vehicle_type': class_name,
                            'vehicle_bbox': [int(x1), int(y1), int(x2), int(y2)]
                        })
    
    return license_plates

def _extract_text_from_license_plate(image: np.ndarray, bbox: List[int]) -> str:
    """Extract text from license plate region using OCR"""
    x1, y1, x2, y2 = bbox
    
    # Extract the license plate region
    plate_region = image[y1:y2, x1:x2]
    
    if plate_region.size == 0:
        return ""
    
    # Convert to PIL Image for better OCR processing
    plate_pil = Image.fromarray(cv2.cvtColor(plate_region, cv2.COLOR_BGR2RGB))
    
    # Preprocess the image for better OCR
    # Convert to grayscale
    gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to get better contrast
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Apply morphological operations to clean up the image
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Use EasyOCR to extract text
    reader = _get_ocr_reader()
    
    try:
        # Run OCR on the cleaned image
        results = reader.readtext(cleaned)
        
        # Combine all detected text
        extracted_text = ""
        for (bbox, text, confidence) in results:
            if confidence > 0.5:  # Only include high-confidence detections
                extracted_text += text + " "
        
        return extracted_text.strip()
    
    except Exception as e:
        print(f"OCR error: {str(e)}")
        return ""

def _detect_license_plates_advanced(image: np.ndarray) -> List[Dict[str, Any]]:
    """Advanced license plate detection using computer vision techniques"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply edge detection
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    license_plates = []
    
    for contour in contours:
        # Approximate the contour
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Check if the contour is roughly rectangular (license plate shape)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            
            # License plates typically have aspect ratios between 2:1 and 5:1
            if 2.0 <= aspect_ratio <= 5.0 and w > 100 and h > 30:
                # Check if the region contains text-like features
                roi = gray[y:y+h, x:x+w]
                
                # Calculate the density of edges in the region
                roi_edges = cv2.Canny(roi, 50, 150)
                edge_density = np.sum(roi_edges > 0) / (w * h)
                
                # License plates should have high edge density due to text
                if edge_density > 0.1:
                    license_plates.append({
                        'bbox': [x, y, x + w, y + h],
                        'confidence': min(edge_density * 2, 1.0),
                        'detection_method': 'cv_contours',
                        'aspect_ratio': aspect_ratio
                    })
    
    return license_plates


@router.get("/detect-license-plates-url", summary="Detect license plates from image URL")
async def detect_license_plates_from_url(
    image_url: str = Query(..., description="URL of the image containing license plates")
) -> Dict[str, Any]:
    """
    Detect license plates from an image URL and extract text
    """
    import requests
    
    try:
        # Fetch the image from URL
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Process the image
        pil_image = Image.open(io.BytesIO(response.content))
        pil_image = pil_image.convert("RGB")
        
        # Convert to OpenCV format
        opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Use the same detection logic as the file upload endpoint
        yolo_plates = _detect_license_plates_yolo(opencv_image)
        cv_plates = _detect_license_plates_advanced(opencv_image)
        
        all_plates = yolo_plates + cv_plates
        
        # Filter duplicates (same logic as above)
        filtered_plates = []
        for plate in all_plates:
            is_duplicate = False
            for existing_plate in filtered_plates:
                bbox1 = plate['bbox']
                bbox2 = existing_plate['bbox']
                
                x1 = max(bbox1[0], bbox2[0])
                y1 = max(bbox1[1], bbox2[1])
                x2 = min(bbox1[2], bbox2[2])
                y2 = min(bbox1[3], bbox2[3])
                
                if x1 < x2 and y1 < y2:
                    overlap_area = (x2 - x1) * (y2 - y1)
                    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
                    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
                    
                    overlap_ratio = overlap_area / min(area1, area2)
                    if overlap_ratio > 0.5:
                        is_duplicate = True
                        if plate['confidence'] > existing_plate['confidence']:
                            filtered_plates.remove(existing_plate)
                            filtered_plates.append(plate)
                        break
            
            if not is_duplicate:
                filtered_plates.append(plate)
        
        # Extract text from each plate
        results = []
        for i, plate in enumerate(filtered_plates):
            bbox = plate['bbox']
            extracted_text = _extract_text_from_license_plate(opencv_image, bbox)
            
            results.append({
                'plate_id': i + 1,
                'bbox': bbox,
                'confidence': plate['confidence'],
                'extracted_text': extracted_text,
                'text_confidence': 0.8 if extracted_text else 0.0,
                'detection_method': plate.get('detection_method', 'yolo'),
                'vehicle_type': plate.get('vehicle_type', 'unknown')
            })
        
        return {
            'message': f'Detected {len(results)} license plate(s) from URL',
            'plates_found': len(results),
            'license_plates': results,
            'image_url': image_url,
            'detection_methods': ['yolo_vehicle_detection', 'cv_contour_analysis', 'easyocr_text_extraction']
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"License plate detection failed: {str(e)}")
