"""
Embedding Service - Generates embeddings for items and queries using OpenAI API.
"""
import logging
import time
from typing import Dict, List, Optional

from openai import OpenAI
from openai import RateLimitError, APIError

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI API."""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.model_name = settings.EMBEDDING_MODEL
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Embedding features will be disabled.")
            return
        
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI client initialized with model: {self.model_name}")
            logger.info(f"Embedding dimension: {self.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model."""
        # text-embedding-3-small: 1536 dimensions
        # text-embedding-3-large: 3072 dimensions
        if "3-small" in self.model_name:
            return 1536
        elif "3-large" in self.model_name:
            return 3072
        else:
            # Default to 1536 for text-embedding-3-small
            return 1536
    
    def _combine_item_text(self, item: Dict) -> str:
        """
        Combine item fields into a single text string for embedding.
        Only includes title and brand for optimal embedding quality.
        
        Args:
            item: Dictionary containing item data
            
        Returns:
            Combined text string
        """
        parts = []
        
        # Add title/name (most important)
        if item.get("title") or item.get("name"):
            parts.append(str(item.get("title") or item.get("name")))
        
        # Add brand (high importance from ML weights: 0.78)
        if item.get("brandName") or item.get("brand_name"):
            brand = item.get("brandName") or item.get("brand_name")
            parts.append(f"Brand: {brand}")
        
        return " ".join(parts)
    
    async def generate_item_embedding(self, item: Dict) -> List[float]:
        """
        Generate embedding for an item using OpenAI API.
        
        Args:
            item: Dictionary containing item data
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.client is None:
            raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")
        
        text = self._combine_item_text(item)
        if not text.strip():
            logger.warning(f"Empty text for item {item.get('itemId') or item.get('id')}, using placeholder")
            text = "item"
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            return response.data[0].embedding
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating embedding for item: {e}")
            raise
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query using OpenAI API.
        
        Args:
            query: Search query text
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.client is None:
            raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")
        
        if not query or not query.strip():
            raise ValueError("Query text cannot be empty")
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=query
            )
            return response.data[0].embedding
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch using OpenAI API.
        OpenAI supports up to 2048 inputs per request.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if self.client is None:
            raise RuntimeError("OpenAI client not initialized. Check OPENAI_API_KEY.")
        
        if not texts:
            return []
        
        # OpenAI batch limit is 2048 inputs per request
        batch_size = 2048
        all_embeddings = []
        
        try:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                try:
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
                    # Rate limit handling: small delay between batches
                    if i + batch_size < len(texts):
                        time.sleep(0.1)
                        
                except RateLimitError as e:
                    logger.warning(f"Rate limit hit, waiting before retry: {e}")
                    time.sleep(1)
                    # Retry the batch
                    response = self.client.embeddings.create(
                        model=self.model_name,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
        except APIError as e:
            logger.error(f"OpenAI API error in batch embeddings: {e}")
            raise
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
        
        return all_embeddings


# Global instance
embedding_service = EmbeddingService()
