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
    """Batch upsert all items to Pinecone using batch embedding generation."""
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
        # OpenAI supports up to 2048 inputs per batch, but we'll use smaller batches
        # to balance memory usage and efficiency
        embedding_batch_size = 500  # Generate embeddings in batches of 500
        pinecone_batch_size = 100   # Upsert to Pinecone in batches of 100
        
        processed = 0
        failed = 0
        
        # Process items in batches for embedding generation
        for i in range(0, len(items), embedding_batch_size):
            batch_items = items[i:i + embedding_batch_size]
            batch_texts = []
            batch_metadata = []
            batch_ids = []
            
            # Prepare texts and metadata for this batch
            for item in batch_items:
                try:
                    # Use the same method as embedding_service to combine text
                    text = embedding_service._combine_item_text(item)
                    if not text.strip():
                        logger.warning(f"Empty text for item {item.get('itemId')}, using placeholder")
                        text = "item"
                    
                    batch_texts.append(text)
                    batch_metadata.append(prepare_metadata(item))
                    batch_ids.append(str(item["itemId"]))
                except Exception as e:
                    logger.error(f"Error preparing item {item.get('itemId')}: {e}")
                    failed += 1
                    continue
            
            if not batch_texts:
                continue
            
            try:
                # Generate embeddings in batch
                logger.info(f"Generating embeddings for batch {i//embedding_batch_size + 1} ({len(batch_texts)} items)...")
                batch_embeddings = await embedding_service.generate_batch_embeddings(batch_texts)
                
                # Prepare vectors for Pinecone
                vectors = []
                for j, (item_id, embedding, metadata) in enumerate(zip(batch_ids, batch_embeddings, batch_metadata)):
                    vectors.append({
                        "id": item_id,
                        "values": embedding,
                        "metadata": metadata
                    })
                
                # Upsert to Pinecone in batches
                for k in range(0, len(vectors), pinecone_batch_size):
                    pinecone_batch = vectors[k:k + pinecone_batch_size]
                    await pinecone_service.upsert_batch_embeddings(pinecone_batch)
                
                processed += len(vectors)
                logger.info(f"Processed {processed}/{len(items)} items")
                
            except Exception as e:
                logger.error(f"Error processing batch starting at index {i}: {e}")
                failed += len(batch_items)
                continue
        
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

