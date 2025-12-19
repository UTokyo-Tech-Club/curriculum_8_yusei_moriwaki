#!/usr/bin/env python3
"""
Batch script to upsert existing items to Pinecone index.

This script:
1. Fetches all items from the database
2. Generates embeddings for each item
3. Upserts embeddings to Pinecone in batches

Usage:
    python scripts/batch_upsert_pinecone.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base import async_session_maker
from app.repositories.item_repository import ItemRepository
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def prepare_metadata(item: dict) -> dict:
    """
    Prepare metadata for Pinecone, filtering out None/null values.
    Pinecone does not allow null values in metadata.
    """
    metadata = {}
    
    # c0_name
    c0_name = item.get("category") or item.get("c0_name")
    if c0_name:
        metadata["c0_name"] = str(c0_name)
    
    # brand_name
    brand_name = item.get("brandName") or item.get("brand_name")
    if brand_name:
        metadata["brand_name"] = str(brand_name)
    
    # condition
    condition = item.get("condition") or item.get("item_condition_name")
    if condition:
        metadata["condition"] = str(condition)
    
    return metadata


async def batch_upsert_items():
    """Batch upsert all items to Pinecone."""
    # Initialize Pinecone
    logger.info("Initializing Pinecone...")
    await pinecone_service.initialize()
    
    if not pinecone_service.initialized:
        logger.error("Pinecone not initialized. Please check PINECONE_API_KEY.")
        return
    
    # Get all items from database
    async with async_session_maker() as db:
        item_repo = ItemRepository(db)
        
        logger.info("Fetching all items from database...")
        # Get all active items
        items = await item_repo.get_items_with_details(
            status="active",
            limit=10000,  # Large limit to get all items
            offset=0
        )
        
        logger.info(f"Found {len(items)} items to process")
        
        if not items:
            logger.info("No items to process")
            return
        
        # Process in batches
        batch_size = 100
        vectors = []
        processed = 0
        failed = 0
        
        for i, item in enumerate(items):
            try:
                # Generate embedding
                embedding = await embedding_service.generate_item_embedding(item)
                
                # Prepare metadata (filter out None/null values)
                metadata = prepare_metadata(item)
                
                # Add to batch
                vectors.append({
                    "id": str(item["itemId"]),
                    "values": embedding,
                    "metadata": metadata
                })
                
                # Upsert batch when full
                if len(vectors) >= batch_size:
                    await pinecone_service.upsert_batch_embeddings(vectors)
                    processed += len(vectors)
                    logger.info(f"Processed {processed}/{len(items)} items")
                    vectors = []
                    
            except Exception as e:
                logger.error(f"Error processing item {item.get('itemId')}: {e}")
                failed += 1
                continue
        
        # Upsert remaining vectors
        if vectors:
            await pinecone_service.upsert_batch_embeddings(vectors)
            processed += len(vectors)
        
        logger.info("Batch upsert complete!")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Failed: {failed}")
        
        # Get index stats
        stats = await pinecone_service.get_index_stats()
        if stats:
            logger.info(f"Pinecone index stats: {stats}")


async def main():
    """Main entry point."""
    try:
        await batch_upsert_items()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in batch upsert: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

