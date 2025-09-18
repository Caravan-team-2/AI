from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict, Any
from PIL import Image
import google.generativeai as genai
import io
import json
import re
from app.core.config import get_settings


router = APIRouter()


def _extract_fields_with_gemini(image: Image.Image) -> Dict[str, Any]:
    """Extract fields from license card image using Gemini Vision API"""
    settings = get_settings()
    

    
    # Configure Gemini
    genai.configure(api_key="AIzaSyAuJLWs0O9vVBPJZaiaZFFfSG238HfqeSU")
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Convert PIL image to bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    # Wrap image correctly for Gemini
    image_blob = {
        "mime_type": "image/png",
        "data": image_bytes
    }

    # Create structured extraction prompt
    prompt = """
    Analyze this Arabic license card image and extract the following information in JSON format:
    {
        "license_number": "extract the license/driving permit number",
        "name": "extract the (name)",
        "surname": "extract the (family name)",
        "date_of_birth": "extract the date of birth",
        "expiry_date": "extract the expiry date",
        "gender": "extract the gender",
		"issue_date": "extract the issue date"
    }

    Rules:
    - Look for name and surname in the image and license number and the date of birth and the expiry date
    - If a field is not found, use null
    - Return only valid JSON, no additional text
    - License number should be numeric only
    - Names should be clean text without extra characters
    - Date of birth and expiry date should be in the format of YYYY-MM-DD
	- all the fields are in Arabic

    """

    try:
        # Send both prompt + image
        response = model.generate_content([prompt, image_blob])
        response_text = response.text.strip()

        # Try parsing JSON
        extracted_data = json.loads(response_text)

        return {
            "license_number": extracted_data.get("license_number"),
            "name": extracted_data.get("name"),
            "surname": extracted_data.get("surname"),
            "date_of_birth": extracted_data.get("date_of_birth"),
            "expiry_date": extracted_data.get("expiry_date"),
            "gender": extracted_data.get("gender"),
            "issue_date": extracted_data.get("issue_date")
        }

    except json.JSONDecodeError:
        # Fallback regex extraction
        license_match = re.search(r'"license_number":\s*"([^"]*)"', response_text)
        name_match = re.search(r'"name":\s*"([^"]*)"', response_text)
        surname_match = re.search(r'"surname":\s*"([^"]*)"', response_text)
        date_of_birth_match = re.search(r'"date_of_birth":\s*"([^"]*)"', response_text)
        expiry_date_match = re.search(r'"expiry_date":\s*"([^"]*)"', response_text)
        gender_match = re.search(r'"gender":\s*"([^"]*)"', response_text)
        issue_date_match = re.search(r'"issue_date":\s*"([^"]*)"', response_text)
        return {
            "license_number": license_match.group(1) if license_match else None,
            "name": name_match.group(1) if name_match else None,
            "surname": surname_match.group(1) if surname_match else None,
            "date_of_birth": date_of_birth_match.group(1) if date_of_birth_match else None,
            "expiry_date": expiry_date_match.group(1) if expiry_date_match else None,
            "gender": gender_match.group(1) if gender_match else None,
            "issue_date": issue_date_match.group(1) if issue_date_match else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


@router.post("/extract", summary="Extract data from Arabic license card image using Gemini")
async def extract_id_data(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await file.read()
    try:
        image = Image.open(io.BytesIO(content))
        image = image.convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Extract fields using Gemini Vision API
    try:
        fields = _extract_fields_with_gemini(image)
        return {"fields": fields, "extraction_method": "gemini_vision"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")