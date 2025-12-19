"""
Pinecone Service - Manages Pinecone index operations for vector storage and search.
"""
import logging
from typing import Dict, List, Optional

from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeException

from app.config import settings

logger = logging.getLogger(__name__)


def _filter_null_metadata(metadata: Dict) -> Dict:
    """
    Filter out None/null values from metadata dictionary.
    Pinecone does not allow null values in metadata.
    
    Args:
        metadata: Metadata dictionary that may contain None values
        
    Returns:
        Dictionary with only non-null values
    """
    filtered = {}
    for key, value in metadata.items():
        if value is not None and value != "":
            # Convert to string if not already
            if isinstance(value, (str, int, float, bool)):
                filtered[key] = value
            elif isinstance(value, list):
                # Filter out None values from lists
                filtered_list = [v for v in value if v is not None]
                if filtered_list:
                    filtered[key] = filtered_list
            else:
                filtered[key] = str(value)
    return filtered


class PineconeService:
    """Service for Pinecone vector database operations."""
    
    def __init__(self):
        self.pc: Optional[Pinecone] = None
        self.index_name = settings.PINECONE_INDEX_NAME
        self.index = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize Pinecone connection and ensure index exists."""
        if self.initialized:
            return
        
        api_key = settings.PINECONE_API_KEY
        if not api_key:
            logger.warning("PINECONE_API_KEY not set. Pinecone features will be disabled.")
            return
        
        try:
            self.pc = Pinecone(api_key=api_key)
            logger.info("Pinecone client initialized")
            
            # Check if index exists, create if not
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                # Get embedding dimension from embedding service
                from app.services.embedding_service import embedding_service
                dimension = embedding_service.get_embedding_dimension()
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric="dotproduct",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created Pinecone index: {self.index_name} with dimension {dimension}")
            else:
                logger.info(f"Pinecone index {self.index_name} already exists")
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            self.initialized = True
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except PineconeException as e:
            logger.error(f"Pinecone error during initialization: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            raise
    
    async def upsert_item_embedding(
        self,
        item_id: int,
        embedding: List[float],
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Upsert an item embedding to Pinecone.
        
        Args:
            item_id: Item ID
            embedding: Embedding vector
            metadata: Optional metadata dictionary
        """
        if not self.initialized or self.index is None:
            logger.warning("Pinecone not initialized. Skipping upsert.")
            return
        
        try:
            metadata = metadata or {}
            metadata["item_id"] = item_id
            
            # Filter out null values from metadata
            filtered_metadata = _filter_null_metadata(metadata)
            
            self.index.upsert(
                vectors=[{
                    "id": str(item_id),
                    "values": embedding,
                    "metadata": filtered_metadata
                }]
            )
            logger.debug(f"Upserted embedding for item {item_id} to Pinecone")
        except Exception as e:
            logger.error(f"Error upserting embedding for item {item_id}: {e}")
            raise
    
    async def upsert_batch_embeddings(
        self,
        vectors: List[Dict]
    ) -> None:
        """
        Upsert multiple embeddings in batch.
        
        Args:
            vectors: List of dictionaries with 'id', 'values', and 'metadata' keys
        """
        if not self.initialized or self.index is None:
            logger.warning("Pinecone not initialized. Skipping batch upsert.")
            return
        
        try:
            # Filter null values from metadata in all vectors
            filtered_vectors = []
            for vector in vectors:
                filtered_vector = vector.copy()
                if "metadata" in filtered_vector:
                    filtered_vector["metadata"] = _filter_null_metadata(filtered_vector["metadata"])
                filtered_vectors.append(filtered_vector)
            
            # Pinecone recommends batches of 100
            batch_size = 100
            for i in range(0, len(filtered_vectors), batch_size):
                batch = filtered_vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.debug(f"Upserted batch {i//batch_size + 1} ({len(batch)} vectors)")
            
            logger.info(f"Upserted {len(vectors)} embeddings to Pinecone")
        except Exception as e:
            logger.error(f"Error in batch upsert: {e}")
            raise
    
    async def search_similar_items(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar items using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filter dictionary
            
        Returns:
            List of dictionaries with 'id', 'score', and 'metadata' keys
        """
        if not self.initialized or self.index is None:
            logger.warning("Pinecone not initialized. Returning empty results.")
            return []
        
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            matches = []
            for match in results.get("matches", []):
                matches.append({
                    "item_id": int(match["id"]),
                    "score": float(match["score"]),
                    "metadata": match.get("metadata", {})
                })
            
            return matches
        except Exception as e:
            logger.error(f"Error searching Pinecone: {e}")
            return []
    
    async def delete_item_embedding(self, item_id: int) -> None:
        """
        Delete an item embedding from Pinecone.
        
        Args:
            item_id: Item ID to delete
        """
        if not self.initialized or self.index is None:
            logger.warning("Pinecone not initialized. Skipping delete.")
            return
        
        try:
            self.index.delete(ids=[str(item_id)])
            logger.debug(f"Deleted embedding for item {item_id} from Pinecone")
        except Exception as e:
            logger.error(f"Error deleting embedding for item {item_id}: {e}")
            # Don't raise - deletion failures are not critical
    
    async def get_index_stats(self) -> Dict:
        """
        Get statistics about the Pinecone index.
        
        Returns:
            Dictionary with index statistics
        """
        if not self.initialized or self.index is None:
            return {}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("index_fullness", 0)
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}


# Global instance
pinecone_service = PineconeService()

