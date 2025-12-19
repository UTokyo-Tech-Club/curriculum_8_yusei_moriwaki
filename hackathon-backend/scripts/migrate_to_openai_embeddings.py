#!/usr/bin/env python3
"""
Migration script to switch from sentence-transformers to OpenAI embeddings.

This script:
1. Deletes the old Pinecone index (optional, can use different index name)
2. Creates a new index with 1536 dimensions (OpenAI text-embedding-3-small)
3. Regenerates all embeddings using OpenAI API
4. Upserts embeddings to the new index

Usage:
    python scripts/migrate_to_openai_embeddings.py [--delete-old-index]
"""
import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.base import async_session_maker
from app.repositories.item_repository import ItemRepository
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_to_openai_embeddings(delete_old_index: bool = False):
    """Migrate Pinecone index to OpenAI embeddings."""
    # Initialize Pinecone
    logger.info("Initializing Pinecone...")
    await pinecone_service.initialize()
    
    if not pinecone_service.initialized:
        logger.error("Pinecone not initialized. Please check PINECONE_API_KEY.")
        return
    
    # Check if OpenAI client is initialized
    if embedding_service.client is None:
        logger.error("OpenAI client not initialized. Please check OPENAI_API_KEY.")
        return
    
    # Verify embedding dimension
    dimension = embedding_service.get_embedding_dimension()
    logger.info(f"Using embedding dimension: {dimension}")
    
    if dimension != 1536:
        logger.warning(f"Expected dimension 1536, but got {dimension}. Continuing anyway...")
    
    # Delete old index if requested
    if delete_old_index:
        logger.info(f"Deleting old index: {pinecone_service.index_name}")
        try:
            pinecone_service.pc.delete_index(pinecone_service.index_name)
            logger.info("Old index deleted. Waiting 10 seconds for deletion to complete...")
            await asyncio.sleep(10)
        except Exception as e:
            logger.warning(f"Could not delete old index (may not exist): {e}")
    
    # Reinitialize to create new index
    pinecone_service.initialized = False
    await pinecone_service.initialize()
    
    if not pinecone_service.initialized:
        logger.error("Failed to initialize Pinecone after migration setup.")
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
                # Generate embedding using OpenAI
                embedding = await embedding_service.generate_item_embedding(item)
                
                # Prepare metadata (filter out None/null values)
                from app.services.item_service import _prepare_pinecone_metadata
                metadata = _prepare_pinecone_metadata(item)
                
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
        
        logger.info("Migration complete!")
        logger.info(f"  Processed: {processed}")
        logger.info(f"  Failed: {failed}")
        
        # Get index stats
        stats = await pinecone_service.get_index_stats()
        if stats:
            logger.info(f"Pinecone index stats: {stats}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate to OpenAI embeddings")
    parser.add_argument(
        "--delete-old-index",
        action="store_true",
        help="Delete the old Pinecone index before creating new one"
    )
    args = parser.parse_args()
    
    try:
        await migrate_to_openai_embeddings(delete_old_index=args.delete_old_index)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in migration: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

