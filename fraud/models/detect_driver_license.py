import numpy as np
from typing import List, Dict, Any
import cv2
import torch
from ultralytics import YOLO

def detect_driver_license(image: np.ndarray) -> List[Dict[str, Any]]:
    """
    Detect driver license in the image and return bounding boxes and confidence scores
    """
    
    # Load model
    model = YOLO("yolov8n.pt")
    
    # Run inference
    results = model(image, conf=0.6)  # confidence threshold
    
    # Filter for objects that might be driver license
    driver_licenses = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                # Get class name
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])
                
                # Filter for driver license class
                if class_name == 'license' and confidence > 0.6:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    driver_licenses.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence,
                    })
    
    return driver_licenses
