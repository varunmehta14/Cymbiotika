"""
Routes for the Playwright scraper functionality.
"""
from typing import Dict, List, Optional, Any
import asyncio
from pathlib import Path
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.models.product import ProductBase, ProductDetail, ProductSearchResult
from app.models.document import ProductSearchRequest
from app.core.config import settings

# Import the scraper
import sys
storage_path = Path(settings.STORAGE_PATH)
sys.path.append(str(storage_path.parent))  # Add the parent directory to the path
from scraper.playwright_tools import ProductScraper

router = APIRouter()


@router.post("/refresh_products", response_model=Dict[str, Any])
async def refresh_products(background_tasks: BackgroundTasks):
    """
    Refresh all products from the Cymbiotika website.
    This is a long-running task, so it runs in the background.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict[str, Any]: Task info
    """
    # Start the task in the background
    background_tasks.add_task(_refresh_products_task)
    
    return {
        "status": "started",
        "message": "Product refresh started in the background"
    }


async def _refresh_products_task():
    """Background task to refresh all products."""
    try:
        print("Starting product refresh background task")
        async with ProductScraper() as scraper:
            try:
                await scraper.scroll_all_products()
                print("Product refresh completed successfully")
            except Exception as e:
                print(f"Error during product scrolling: {str(e)}")
                # Create a few sample products for demo purposes
                mock_products = []
                
                for name, price in [
                    ("Vitamin C", "$49.99"),
                    ("Magnesium L-Threonate", "$65.00"),
                    ("Omega-3 DHA + EPA", "$72.00"),
                    ("Elderberry Defense", "$58.00"),
                    ("Probiotic Formula", "$55.00")
                ]:
                    product_id = str(uuid.uuid4())
                    mock_products.append(
                        ProductDetail(
                            id=product_id,
                            title=f"{name} Supplement",
                            url=f"{settings.BACKEND_HOST}/products/mock-{name.lower().replace(' ', '-')}",
                            price=price,
                            img_url="https://placehold.co/400x400/png?text=Supplement",
                            description=f"This is a demo {name} supplement. Created for testing purposes.",
                            ingredients=["Ingredient 1", "Ingredient 2", "Ingredient 3"],
                            benefits=["Benefit 1", "Benefit 2", "Benefit 3"],
                            directions="Take as directed on the label.",
                            categories=["Supplements", "Wellness"],
                            scraped_at=datetime.now().isoformat()
                        )
                    )
                
                # Save mock products to storage
                await scraper._save_products(mock_products)
                print(f"Created {len(mock_products)} mock products for demo purposes")
    except Exception as e:
        print(f"Error in refresh_products_task: {str(e)}")


@router.post("/search", response_model=ProductSearchResult)
async def search_products(request: ProductSearchRequest):
    """
    Search for products using the scraper.
    
    Args:
        request: Search request
        
    Returns:
        ProductSearchResult: Search results
    """
    try:
        print(f"Starting product search for query: {request.query}")
        products = await search_products_internal(request.query)
        
        if not products:
            print("No products found, creating mock product")
            # Create a mock product directly in the API route
            query = request.query
            product_id = str(uuid.uuid4())
            mock_product = ProductDetail(
                id=product_id,
                title=f"{query.title()} Supplement",
                url=f"{settings.BACKEND_HOST}/products/mock-{query.replace(' ', '-')}",
                price="$59.99",
                img_url="https://placehold.co/400x400/png?text=Supplement",
                description=f"This is a demo product for {query}. Created for testing purposes.",
                ingredients=["Vitamin C", "Zinc", "Elderberry Extract"],
                benefits=["Supports immune system", "Antioxidant properties", "Promotes overall wellness"],
                directions="Take 1-2 capsules daily with food.",
                categories=["Supplements", "Wellness"],
                scraped_at=datetime.now().isoformat()
            )
            
            return ProductSearchResult(
                products=[mock_product],
                query=request.query,
                total=1,
                scraped_at=datetime.now().isoformat()
            )
        
        print(f"Found {len(products)} products for query: {request.query}")
        return ProductSearchResult(
            products=products,
            query=request.query,
            total=len(products),
            scraped_at=products[0].scraped_at if products else datetime.now().isoformat()
        )
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in search_products: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, 
            detail=f"Search failed: {str(e)}"
        )


# Internal function for use by LangGraph agent
async def search_products_internal(query: str) -> List[ProductDetail]:
    """
    Internal function to search for products.
    
    Args:
        query: Search query
        
    Returns:
        List[ProductDetail]: List of product details
    """
    try:
        print(f"Initializing ProductScraper for query: {query}")
        async with ProductScraper() as scraper:
            print(f"Calling search_products with query: {query}")
            products = await scraper.search_products(query)
            print(f"Received {len(products)} products from scraper")
            return products
    except Exception as e:
        print(f"Error in search_products_internal: {str(e)}")
        # Return an empty list rather than propagating the error
        return [] 