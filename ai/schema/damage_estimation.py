from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DamageSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


class PartCategory(str, Enum):
    BODY_PANEL = "Body Panel"
    LIGHTING = "Lighting"
    GLASS = "Glass"
    MIRROR = "Mirror"
    DOOR = "Door"
    BUMPER = "Bumper"
    WHEEL = "Wheel"
    TIRE = "Tire"
    OTHER = "Other"


class CarDetails(BaseModel):
    make: Optional[str] = Field(None, description="Car make (e.g., Toyota, Honda)")
    model: Optional[str] = Field(None, description="Car model (e.g., Camry, Civic)")
    year: Optional[str] = Field(None, description="Car year (e.g., 2020, 2018)")


class PriceSearchResults(BaseModel):
    min_price: float = Field(..., description="Minimum price found in USD")
    max_price: float = Field(..., description="Maximum price found in USD")
    avg_price: float = Field(..., description="Average price in USD")
    price_count: int = Field(..., description="Number of prices found")
    currency: str = Field(default="USD", description="Currency code")


class DamagedPart(BaseModel):
    part_name: str = Field(..., description="Name of the damaged part")
    part_category: PartCategory = Field(..., description="Category of the part")
    damage_type: str = Field(..., description="Type of damage")
    severity: DamageSeverity = Field(..., description="Severity of damage")
    car_details: CarDetails = Field(..., description="Car information")
    viewing_angle: Optional[str] = Field(None, description="Angle from which damage was observed")


class PartPriceSearch(BaseModel):
    part_name: str = Field(..., description="Name of the damaged part")
    part_category: str = Field(..., description="Category of the part")
    damage_type: str = Field(..., description="Type of damage")
    severity: DamageSeverity = Field(..., description="Severity of damage")
    car_details: CarDetails = Field(..., description="Car information")
    viewing_angle: Optional[str] = Field(None, description="Angle from which damage was observed")
    price_search_results: PriceSearchResults = Field(..., description="Price search results")
    search_successful: bool = Field(..., description="Whether price search was successful")
    error: Optional[str] = Field(None, description="Error message if search failed")


class TotalCostEstimate(BaseModel):
    min: float = Field(..., description="Minimum total cost in USD")
    max: float = Field(..., description="Maximum total cost in USD")
    avg: float = Field(..., description="Average total cost in USD")
    currency: str = Field(default="USD", description="Currency code")


class PriceSearchResponse(BaseModel):
    message: str = Field(..., description="Summary message")
    parts_found: int = Field(..., description="Number of damaged parts found")
    successful_price_searches: int = Field(..., description="Number of successful price searches")
    price_searches: List[PartPriceSearch] = Field(..., description="Price search results for each part")
    total_estimated_cost: TotalCostEstimate = Field(..., description="Total cost estimate")
    analysis_method: str = Field(..., description="Method used for analysis")


class MultiAnglePriceSearchResponse(BaseModel):
    message: str = Field(..., description="Summary message")
    parts_found: int = Field(..., description="Number of damaged parts found")
    successful_price_searches: int = Field(..., description="Number of successful price searches")
    angles_analyzed: List[str] = Field(..., description="List of angles that were analyzed")
    price_searches: List[PartPriceSearch] = Field(..., description="Price search results for each part")
    total_estimated_cost: TotalCostEstimate = Field(..., description="Total cost estimate")
    analysis_method: str = Field(..., description="Method used for analysis")


class ImageInfo(BaseModel):
    angle: str = Field(..., description="Viewing angle of the image")
    filename: Optional[str] = Field(None, description="Original filename")
    content_type: Optional[str] = Field(None, description="MIME type of the image")
    size_bytes: Optional[int] = Field(None, description="Size of the image in bytes")


class PriceSearchError(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")