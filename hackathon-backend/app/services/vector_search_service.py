"""
Vector Search Service - Orchestrates the full vector search pipeline.
"""
import logging
from typing import Dict, List, Optional, Any

from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.services.similarity_service import similarity_service

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for orchestrating vector search operations."""
    
    def __init__(self, item_repository):
        self.item_repo = item_repository
    
    async def search_similar_items(
        self,
        query: Optional[str] = None,
        item_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for similar items using vector similarity and weighted features.
        
        Args:
            query: Optional text query string
            item_id: Optional item ID to find similar items to
            category: Optional category filter
            limit: Maximum number of results to return
            
        Returns:
            List of item dictionaries sorted by similarity score
        """
        # Determine query embedding
        query_embedding = None
        query_item = None
        
        if item_id:
            # Get the item to use as query
            query_item = await self.item_repo.get_item_with_details_by_item_id(item_id)
            if not query_item:
                logger.warning(f"Item {item_id} not found")
                return []
            
            # Generate embedding from item text
            query_embedding = await embedding_service.generate_item_embedding(query_item)
        elif query:
            # Generate embedding from query text
            query_embedding = await embedding_service.generate_query_embedding(query)
            # For feature matching, we'll use a minimal query item
            query_item = {"name": query, "category": category or ""}
        else:
            logger.warning("Either query or item_id must be provided")
            return []
        
        # Search Pinecone
        top_k = min(limit * 3, 100)  # Get more candidates for re-ranking
        # Note: Category filtering will be done post-query for simplicity
        # Pinecone metadata filtering can be added later if needed
        
        pinecone_results = await pinecone_service.search_similar_items(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_dict=None  # Filter by category in post-processing
        )
        
        # Filter by category if specified (post-processing)
        if category:
            c0_names = self.item_repo._reverse_map_category(category)
            # Filter results that match category (will be refined after DB lookup)
            pass  # Category filtering happens after DB lookup
        
        if not pinecone_results:
            logger.info("No results from Pinecone")
            return []
        
        # Get full item details from database
        item_ids = [r["item_id"] for r in pinecone_results]
        candidate_items = await self.item_repo.get_items_by_item_ids(item_ids)
        
        # Also add category info from mercari_items for feature matching
        for item in candidate_items:
            # Ensure we have category fields for similarity calculation
            if not item.get("c0_name") and item.get("category"):
                # Reverse map category back to c0_name if needed
                pass  # Will be handled by similarity service
        
        # Create mapping from item_id to item
        item_map = {item["itemId"]: item for item in candidate_items}
        
        # Filter to items that exist in database and extract vector scores
        valid_items = []
        vector_scores = []
        for result in pinecone_results:
            item_id = result["item_id"]
            if item_id in item_map:
                item = item_map[item_id]
                # Apply category filter if specified
                if category:
                    item_category = item.get("category", "")
                    if item_category.lower() != category.lower():
                        continue
                valid_items.append(item)
                vector_scores.append(result["score"])
        
        if not valid_items:
            logger.info("No valid items found after database lookup")
            return []
        
        # Calculate hybrid similarity
        # Use query_item if we have it (from item_id search), otherwise use query text
        if query_item and query_item.get("itemId"):
            # Use full query item for feature matching
            full_query_item = query_item
        elif query_item:
            # Query text case - use minimal query item
            full_query_item = query_item
        else:
            # Fallback: use first candidate as reference
            full_query_item = valid_items[0] if valid_items else {}
        
        ranked_results = await similarity_service.calculate_hybrid_similarity(
            query_item=full_query_item,
            candidate_items=valid_items,
            vector_similarities=vector_scores
        )
        
        # Return top N results
        return [item for item, score in ranked_results[:limit]]


