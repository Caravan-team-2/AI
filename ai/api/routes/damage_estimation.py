from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from typing import Dict, Any, List, Optional
from PIL import Image
import google.generativeai as genai
import io
import json
import re
import httpx
from ai.core.config import get_settings

router = APIRouter()


def _identify_damaged_parts_with_gemini(image: Image.Image, angle: str = "unknown") -> List[Dict[str, Any]]:
    """Identify damaged car parts from image using Gemini Vision API"""
    settings = get_settings()
    
    # Configure Gemini
    genai.configure(api_key="AIzaSyAuJLWs0O9vVBPJZaiaZFFfSG238HfqeSU")
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Convert PIL image to bytesllmmmm
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_bytes = buffer.getvalue()

    # Wrap image correctly for Gemini
    image_blob = {
        "mime_type": "image/png",
        "data": image_bytes
    }

    # Create focused prompt for part identification
    prompt = f"""
    Analyze this car damage image (viewing angle: {angle}) and identify ONLY the damaged car parts in JSON format:
    {
        "damaged_parts": [
            {
                "part_name": "exact name of the damaged part (e.g., 'Front Bumper', 'Left Headlight', 'Windshield')",
                "part_category": "category (e.g., 'Body Panel', 'Lighting', 'Glass', 'Mirror', 'Door')",
                "damage_type": "type of damage (e.g., 'crack', 'dent', 'scratch', 'broken')",
                "severity": "minor|moderate|severe",
                "car_make": "car make if visible (e.g., 'Toyota', 'Honda', 'BMW')",
                "car_model": "car model if visible (e.g., 'Camry', 'Civic', 'X5')",
                "car_year": "year if visible (e.g., '2020', '2018')"
            }
        ]
    }

    Rules:
    - Identify ONLY damaged parts, ignore undamaged areas
    - Use specific part names (e.g., "Front Bumper" not just "bumper")
    - Include car details if visible in the image
    - Be precise with part names for accurate price searching
    - If no damage is visible, return empty array
    - Return only valid JSON, no additional text
    - Focus on parts that would need replacement or repair
    """

    try:
        # Send both prompt + image
        response = model.generate_content([prompt, image_blob])
        response_text = response.text.strip()

        # Try parsing JSON
        extracted_data = json.loads(response_text)
        return extracted_data.get("damaged_parts", [])

    except json.JSONDecodeError:
        # Fallback regex extraction
        parts_match = re.search(r'"damaged_parts":\s*\[(.*?)\]', response_text, re.DOTALL)
        if parts_match:
            return []
        return []

    except Exception as e:
        print(f"Error identifying parts: {str(e)}")
        return []


async def _search_part_prices(part_info: Dict[str, Any]) -> Dict[str, Any]:
    """Search for real-time prices of damaged car parts"""
    part_name = part_info.get("part_name", "")
    car_make = part_info.get("car_make", "")
    car_model = part_info.get("car_model", "")
    car_year = part_info.get("car_year", "")
    
    # Create search query
    search_terms = [part_name]
    if car_make:
        search_terms.append(car_make)
    if car_model:
        search_terms.append(car_model)
    if car_year:
        search_terms.append(car_year)
    
    search_query = " ".join(search_terms) + " car part price replacement cost"
    
    try:
        # Search for part prices using web search
        async with httpx.AsyncClient() as client:
            # Search multiple sources for better price coverage
            search_urls = [
                f"https://www.google.com/search?q={search_query}+site:autoparts.com",
                f"https://www.google.com/search?q={search_query}+site:rockauto.com",
                f"https://www.google.com/search?q={search_query}+site:partsgeek.com",
                f"https://www.google.com/search?q={search_query}+site:amazon.com"
            ]
            
            price_results = []
            
            for url in search_urls:
                try:
                    response = await client.get(url, timeout=10.0)
                    if response.status_code == 200:
                        # Extract price information from search results
                        content = response.text
                        
                        # Look for price patterns
                        price_patterns = [
                            r'\$[\d,]+\.?\d*',  # $123.45 or $1,234
                            r'USD\s*[\d,]+\.?\d*',  # USD 123.45
                            r'Price:\s*\$?[\d,]+\.?\d*',  # Price: $123.45
                        ]
                        
                        for pattern in price_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in matches:
                                # Clean and extract numeric value
                                price_str = re.sub(r'[^\d.]', '', match)
                                if price_str and '.' in price_str:
                                    try:
                                        price = float(price_str)
                                        if 10 <= price <= 5000:  # Reasonable price range
                                            price_results.append(price)
                                    except ValueError:
                                        continue
                except Exception:
                    continue
            
            if price_results:
                # Calculate price statistics
                min_price = min(price_results)
                max_price = max(price_results)
                avg_price = sum(price_results) / len(price_results)
                
                return {
                    "part_name": part_name,
                    "part_category": part_info.get("part_category", ""),
                    "damage_type": part_info.get("damage_type", ""),
                    "severity": part_info.get("severity", ""),
                    "car_details": {
                        "make": car_make,
                        "model": car_model,
                        "year": car_year
                    },
                    "price_search_results": {
                        "min_price": round(min_price, 2),
                        "max_price": round(max_price, 2),
                        "avg_price": round(avg_price, 2),
                        "price_count": len(price_results),
                        "currency": "USD"
                    },
                    "search_successful": True
                }
            else:
                return {
                    "part_name": part_name,
                    "part_category": part_info.get("part_category", ""),
                    "damage_type": part_info.get("damage_type", ""),
                    "severity": part_info.get("severity", ""),
                    "car_details": {
                        "make": car_make,
                        "model": car_model,
                        "year": car_year
                    },
                    "price_search_results": {
                        "min_price": 0,
                        "max_price": 0,
                        "avg_price": 0,
                        "price_count": 0,
                        "currency": "USD"
                    },
                    "search_successful": False,
                    "error": "No prices found for this part"
                }
    
    except Exception as e:
        return {
            "part_name": part_name,
            "part_category": part_info.get("part_category", ""),
            "damage_type": part_info.get("damage_type", ""),
            "severity": part_info.get("severity", ""),
            "car_details": {
                "make": car_make,
                "model": car_model,
                "year": car_year
            },
            "price_search_results": {
                "min_price": 0,
                "max_price": 0,
                "avg_price": 0,
                "price_count": 0,
                "currency": "USD"
            },
            "search_successful": False,
            "error": f"Search failed: {str(e)}"
        }
@router.post("/search-multi-angle-prices", summary="Search for damaged part prices from multiple angles")
async def search_multi_angle_prices(
    front_image: UploadFile = File(..., description="Front view of the car"),
    back_image: UploadFile = File(..., description="Back view of the car"),
    left_image: UploadFile = File(..., description="Left side view of the car"),
    right_image: UploadFile = File(..., description="Right side view of the car")
) -> Dict[str, Any]:
    """
    Deep search for damaged car part prices from multiple angles:
    - Analyzes front, back, left, and right views
    - Identifies all damaged parts across all angles
    - Searches real-time prices for each damaged part
    - Provides comprehensive cost estimation
    """
    # Validate all files are images
    files = [front_image, back_image, left_image, right_image]
    angles = ["front", "back", "left", "right"]
    
    for file, angle in zip(files, angles):
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"{angle} file must be an image")
    
    all_damaged_parts = []
    images_data = []
    
    # Process each image and identify damaged parts
    for file, angle in zip(files, angles):
        try:
            content = await file.read()
            image = Image.open(io.BytesIO(content))
            image = image.convert("RGB")
            
            # Identify damaged parts for this angle
            damaged_parts = _identify_damaged_parts_with_gemini(image, angle)
            
            # Add angle information to each part
            for part in damaged_parts:
                part["viewing_angle"] = angle
                all_damaged_parts.append(part)
            
            images_data.append({
                "angle": angle,
                "filename": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(content)
            })
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid {angle} image file: {str(e)}")
    
    if not all_damaged_parts:
        return {
            "message": "No damaged parts identified in any of the images",
            "parts_found": 0,
            "angles_analyzed": [img["angle"] for img in images_data],
            "price_searches": [],
            "total_estimated_cost": {
                "min": 0,
                "max": 0,
                "avg": 0,
                "currency": "USD"
            }
        }
    
    try:
        # Search prices for all damaged parts
        price_searches = []
        total_min = 0
        total_max = 0
        successful_searches = 0
        
        for part in all_damaged_parts:
            price_result = await _search_part_prices(part)
            price_searches.append(price_result)
            
            if price_result.get("search_successful", False):
                total_min += price_result["price_search_results"]["min_price"]
                total_max += price_result["price_search_results"]["max_price"]
                successful_searches += 1
        
        total_avg = (total_min + total_max) / 2 if successful_searches > 0 else 0
        
        return {
            "message": f"Found {len(all_damaged_parts)} damaged parts across {len(angles)} angles, {successful_searches} with price data",
            "parts_found": len(all_damaged_parts),
            "successful_price_searches": successful_searches,
            "angles_analyzed": [img["angle"] for img in images_data],
            "price_searches": price_searches,
            "total_estimated_cost": {
                "min": round(total_min, 2),
                "max": round(total_max, 2),
                "avg": round(total_avg, 2),
                "currency": "USD"
            },
            "analysis_method": "gemini_vision_multi_angle_price_search"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-angle price search failed: {str(e)}")