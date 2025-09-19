from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
from PIL import Image
import google.generativeai as genai
import io
import json
import re
import requests
from ai.core.config import get_settings

router = APIRouter()


def _extract_fields_with_gemini(image: Image.Image,perssonal_image= Image.Image) -> Dict[str, Any]:
    """Extract fields from license card image using Gemini Vision API"""
    settings = get_settings()

    # Configure Gemini
    genai.configure(api_key="AIzaSyD2yJl7z6etVLdW1_CzQ_r4n8JkgdlTXHg")
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Convert PIL image to bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()
    buffer = io.BytesIO()
    perssonal_image.save(buffer, format="PNG")
    perssonal_image_bytes = buffer.getvalue()
    image_blob = {
        "mime_type": "image/png",
        "data": image_bytes
    }

    perssonal_image_blob = {
        "mime_type": "image/png",
        "data": perssonal_image_bytes
    }

    prompt = """
    Analyze this Arabic license card image and extract the following information in JSON format:
    {
        "nin": "national identification number or license number (usually under the birth date)",
        "first_name": "given name",
        "last_name": "family name",
        "dob": "date of birth in YYYY-MM-DD format",
        "sex": "gender",
        "place_of_birth": "place of birth",
        "issued_at": "license issue date in YYYY-MM-DD",
        "expires_at": "license expiry date in YYYY-MM-DD",
        "license_type": "type of license (enum if available)",
        "license_number": "driving license number(ussualy the first code in the license number)",
        "is_verified": "boolean: true if this is a driving license, false if it is any other type of document and the perssonal image is the same as the image of the license card"
    }

    Rules:
    1. All fields must be in Arabic.
    2. If a field is not found, use null, except "is_verified".
    3. "is_verified" must always be true or false. Determine it based on whether the image is a driving license and the perssonal image is the same as the image of the license card.
    4. Return only valid JSON. Do not include explanations or extra text.
    5. If unsure, set "is_verified" to false.
    """

    try:
        response = model.generate_content([prompt, image_blob, perssonal_image_blob])
        response_text = response.text.strip()
        extracted_data = json.loads(response_text)

        nin = extracted_data.get("nin")
        license_number = extracted_data.get("license_number")
        
        return {
            "nin": nin,
            "firstName": extracted_data.get("first_name"),
            "lastName": extracted_data.get("last_name"),
            "dob": extracted_data.get("dob"),
            "sex": extracted_data.get("sex"),
            "placeOfBirth": extracted_data.get("place_of_birth"),
            "issuedAt": extracted_data.get("issued_at"),
            "expiresAt": extracted_data.get("expires_at"),
            "licenseType": extracted_data.get("license_type"),
            "licenseNumber": license_number,
            "is_verified": bool(nin and license_number)
        }

    except json.JSONDecodeError:
        # Fallback: parse manually and ensure is_verified is boolean
        def extract_field(field):
            match = re.search(fr'"{field}":\s*"([^"]*)"', response_text)
            return match.group(1) if match else None

        nin = extract_field("nin")
        license_number = extract_field("license_number")
        
        return {
            "nin": nin,
            "firstName": extract_field("first_name"),
            "lastName": extract_field("last_name"),
            "dob": extract_field("dob"),
            "sex": extract_field("sex"),
            "placeOfBirth": extract_field("place_of_birth"),
            "issuedAt": extract_field("issued_at"),
            "expiresAt": extract_field("expires_at"),
            "licenseType": extract_field("license_type"),
            "licenseNumber": license_number,
            "is_verified": bool(nin and license_number)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


@router.get("/extract", summary="Extract data from Arabic license card image URL using Gemini")
async def extract_id_data_by_url(image_url: str = Query(..., description="Cloudinary image URL"),perssonal_image_url: str = Query(..., description="Cloudinary personal image URL")) -> Dict[str, Any]:
    try:
        # Fetch the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unable to fetch or open image from URL")

    # Extract fields using Gemini Vision API
    try:
        fields = _extract_fields_with_gemini(image,perssonal_image)
        return {"fields": fields, "extraction_method": "gemini_vision"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
