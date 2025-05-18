"""
Product models for supplement data.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl


class ProductBase(BaseModel):
    """
    Base model for product data.
    """
    id: str
    title: str
    url: str
    price: str
    img_url: Optional[str] = None


class ProductDetail(ProductBase):
    """
    Detailed product model with full information.
    """
    description: str
    ingredients: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    directions: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    raw_html: Optional[str] = None
    scraped_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProductSearchResult(BaseModel):
    """
    Model for product search results.
    """
    products: List[ProductDetail]
    query: str
    total: int
    scraped_at: Optional[str] = None
    
    class Config:
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SupplementBundle(BaseModel):
    """
    Model for personalized supplement bundle recommendations.
    """
    products: List[ProductDetail]
    total_price: str
    reasoning: str
    benefits: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow) 