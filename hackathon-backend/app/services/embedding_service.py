"""
Embedding Service - Generates embeddings for items and queries using sentence-transformers.
"""
import logging
from typing import Dict, List, Optional

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.model: Optional[SentenceTransformer] = None
        self.model_name = settings.EMBEDDING_MODEL
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence-transformers model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully. Dimension: {self.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Error loading embedding model {self.model_name}: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model."""
        if self.model is None:
            return 384  # Default for all-MiniLM-L6-v2
        return self.model.get_sentence_embedding_dimension()
    
    def _combine_item_text(self, item: Dict) -> str:
        """
        Combine item fields into a single text string for embedding.
        
        Args:
            item: Dictionary containing item data
            
        Returns:
            Combined text string
        """
        parts = []
        
        # Add title/name
        if item.get("title") or item.get("name"):
            parts.append(str(item.get("title") or item.get("name")))
        
        # Add description
        if item.get("description"):
            parts.append(str(item["description"]))
        
        # Add category information
        if item.get("category"):
            parts.append(f"Category: {item['category']}")
        if item.get("c0_name"):
            parts.append(f"Category: {item['c0_name']}")
        if item.get("c1_name"):
            parts.append(f"Subcategory: {item['c1_name']}")
        if item.get("c2_name"):
            parts.append(f"Subcategory: {item['c2_name']}")
        
        # Add brand
        if item.get("brandName") or item.get("brand_name"):
            parts.append(f"Brand: {item.get('brandName') or item.get('brand_name')}")
        
        # Add condition
        if item.get("condition") or item.get("item_condition_name"):
            parts.append(f"Condition: {item.get('condition') or item.get('item_condition_name')}")
        
        # Add size
        if item.get("size_name"):
            parts.append(f"Size: {item['size_name']}")
        
        return " ".join(parts)
    
    async def generate_item_embedding(self, item: Dict) -> List[float]:
        """
        Generate embedding for an item.
        
        Args:
            item: Dictionary containing item data
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        text = self._combine_item_text(item)
        if not text.strip():
            logger.warning(f"Empty text for item {item.get('itemId') or item.get('id')}, using placeholder")
            text = "item"
        
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding for item: {e}")
            raise
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        if not query or not query.strip():
            raise ValueError("Query text cannot be empty")
        
        try:
            embedding = self.model.encode(query, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            raise RuntimeError("Embedding model not loaded")
        
        try:
            embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise


# Global instance
embedding_service = EmbeddingService()

