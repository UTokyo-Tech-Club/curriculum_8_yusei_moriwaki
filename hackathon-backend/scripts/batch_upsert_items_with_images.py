#!/usr/bin/env python3
"""
Batch script to upsert items to Cloud SQL with images to Supabase Storage.

This script:
1. Reads item data from JSON file
2. Uploads images to Supabase Storage
3. Creates or updates items in Cloud SQL with image URLs

Usage:
    python scripts/batch_upsert_items_with_images.py --input items.json

JSON Format:
    {
        "items": [
            {
                "item_id": 123456789,  # Optional: for updating existing items
                "title": "Item Title",
                "description": "Item description",
                "price": 1000.0,
                "category": "fashion",
                "condition": "Good",
                "brand_name": "Brand Name",
                "seller_user_id": 45,
                "image_path": "./images/item-123.jpg"  # Local file path
            }
        ]
    }
"""
import asyncio
import json
import logging
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base import async_session_maker
from app.repositories.item_repository import ItemRepository
from app.services.supabase_service import supabase_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_items_from_json(json_path: str) -> List[Dict[str, Any]]:
    """Load items from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'items' not in data:
        raise ValueError("JSON file must contain 'items' array")
    
    return data['items']


async def upload_image_to_supabase(image_path: str) -> Optional[str]:
    """Upload image to Supabase Storage and return public URL."""
    try:
        image_file = Path(image_path)
        
        if not image_file.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None
        
        # Read image file
        with open(image_file, 'rb') as f:
            image_bytes = f.read()
        
        # Determine content type from extension
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        content_type = content_type_map.get(image_file.suffix.lower(), 'image/jpeg')
        
        # Upload to Supabase
        image_url = supabase_service.upload_image(
            file_bytes=image_bytes,
            filename=image_file.name,
            content_type=content_type
        )
        
        logger.info(f"Uploaded image: {image_path} -> {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"Error uploading image {image_path}: {e}")
        return None


async def create_or_update_item(
    item_repo: ItemRepository,
    item_data: Dict[str, Any],
    image_url: Optional[str]
) -> bool:
    """Create or update item in database."""
    try:
        item_id = item_data.get('item_id')
        
        if item_id:
            # Update existing item
            # Find listing by item_id (not listing_id)
            from app.models.item_listing import ItemListing
            from sqlalchemy import select
            
            result = await item_repo.db.execute(
                select(ItemListing).where(ItemListing.item_id == item_id)
            )
            listing = result.scalar_one_or_none()
            
            if listing:
                # Update existing listing
                await item_repo.update_listing(
                    listing_id=listing.id,
                    image_url=image_url
                )
                logger.info(f"Updated item {item_id} (listing_id={listing.id}) with image URL")
                return True
            else:
                logger.warning(f"Item {item_id} not found, creating new item")
                # Fall through to create new item
        
        # Create new item
        seller_user_id = item_data.get('seller_user_id')
        if not seller_user_id:
            logger.error("seller_user_id is required for new items")
            return False
        
        listing = await item_repo.create_item_with_listing(
            seller_user_id=seller_user_id,
            title=item_data.get('title', 'Untitled Item'),
            description=item_data.get('description', ''),
            price=item_data.get('price', 0.0),
            category=item_data.get('category', 'other'),
            condition=item_data.get('condition', 'Good'),
            brand_name=item_data.get('brand_name'),
            images=[],
            image_url=image_url
        )
        
        logger.info(f"Created new item with listing_id={listing.id}, item_id={listing.item_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating/updating item: {e}")
        return False


async def batch_upsert_items_with_images(json_path: str):
    """Batch upsert items with images."""
    # Load items from JSON
    logger.info(f"Loading items from {json_path}...")
    items = load_items_from_json(json_path)
    logger.info(f"Loaded {len(items)} items")
    
    if not items:
        logger.info("No items to process")
        return
    
    # Process items
    async with async_session_maker() as db:
        item_repo = ItemRepository(db)
        
        processed = 0
        failed = 0
        
        for i, item_data in enumerate(items, 1):
            logger.info(f"Processing item {i}/{len(items)}: {item_data.get('title', 'Unknown')}")
            
            # Upload image if path provided
            image_url = None
            image_path = item_data.get('image_path')
            if image_path:
                image_url = await upload_image_to_supabase(image_path)
                if not image_url:
                    logger.warning(f"Failed to upload image for item {i}, continuing without image")
            
            # Create or update item
            success = await create_or_update_item(
                item_repo,
                item_data,
                image_url
            )
            
            if success:
                processed += 1
            else:
                failed += 1
        
        logger.info("=" * 80)
        logger.info("Batch upsert complete!")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Failed: {failed}")
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Batch upsert items with images to Cloud SQL and Supabase'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to JSON file containing items data'
    )
    
    args = parser.parse_args()
    
    json_path = Path(args.input)
    if not json_path.exists():
        logger.error(f"JSON file not found: {json_path}")
        sys.exit(1)
    
    try:
        await batch_upsert_items_with_images(str(json_path))
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in batch upsert: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

