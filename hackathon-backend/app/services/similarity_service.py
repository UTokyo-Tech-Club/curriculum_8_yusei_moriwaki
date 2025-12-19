"""
Similarity Service - Calculates hybrid similarity combining vector similarity with weighted features.
"""
import logging
from typing import Dict, List, Tuple, Optional

from app.config import settings
from app.services.ml_weights_service import ml_weights_service

logger = logging.getLogger(__name__)


class SimilarityService:
    """Service for calculating hybrid similarity scores."""
    
    def __init__(self):
        self.vector_weight = settings.VECTOR_WEIGHT
        self.feature_weight = settings.FEATURE_WEIGHT
        # Normalize weights to sum to 1.0
        total = self.vector_weight + self.feature_weight
        if total > 0:
            self.vector_weight /= total
            self.feature_weight /= total
    
    def _calculate_weighted_features(
        self,
        query_item: Dict,
        candidate_item: Dict,
        weights: Dict[str, float]
    ) -> float:
        """
        Calculate weighted feature match score between two items.
        
        Args:
            query_item: Query/reference item dictionary
            candidate_item: Candidate item dictionary
            weights: Dictionary of feature weights from ML model
            
        Returns:
            Weighted feature score (0.0 to 1.0)
        """
        score = 0.0
        total_weight = 0.0
        
        # Category level 0 (c0)
        if weights.get("c0", 0) > 0:
            query_c0 = query_item.get("c0_name") or query_item.get("category", "")
            candidate_c0 = candidate_item.get("c0_name") or candidate_item.get("category", "")
            if query_c0 and candidate_c0 and query_c0.lower() == candidate_c0.lower():
                score += weights["c0"]
            total_weight += weights["c0"]
        
        # Category level 1 (c1)
        if weights.get("c1", 0) > 0:
            query_c1 = query_item.get("c1_name", "")
            candidate_c1 = candidate_item.get("c1_name", "")
            if query_c1 and candidate_c1 and query_c1.lower() == candidate_c1.lower():
                score += weights["c1"]
            total_weight += weights["c1"]
        
        # Category level 2 (c2)
        if weights.get("c2", 0) > 0:
            query_c2 = query_item.get("c2_name", "")
            candidate_c2 = candidate_item.get("c2_name", "")
            if query_c2 and candidate_c2 and query_c2.lower() == candidate_c2.lower():
                score += weights["c2"]
            total_weight += weights["c2"]
        
        # Brand
        if weights.get("brand", 0) > 0:
            query_brand = query_item.get("brandName") or query_item.get("brand_name", "")
            candidate_brand = candidate_item.get("brandName") or candidate_item.get("brand_name", "")
            if query_brand and candidate_brand and query_brand.lower() == candidate_brand.lower():
                score += weights["brand"]
            total_weight += weights["brand"]
        
        # Condition
        if weights.get("condition", 0) > 0:
            query_condition = query_item.get("condition") or query_item.get("item_condition_name", "")
            candidate_condition = candidate_item.get("condition") or candidate_item.get("item_condition_name", "")
            if query_condition and candidate_condition and query_condition.lower() == candidate_condition.lower():
                score += weights["condition"]
            total_weight += weights["condition"]
        
        # Size
        if weights.get("size", 0) > 0:
            query_size = query_item.get("size_name", "")
            candidate_size = candidate_item.get("size_name", "")
            if query_size and candidate_size and query_size.lower() == candidate_size.lower():
                score += weights["size"]
            total_weight += weights["size"]
        
        # Normalize by total weight
        if total_weight > 0:
            return score / total_weight
        return 0.0
    
    async def calculate_hybrid_similarity(
        self,
        query_item: Optional[Dict],
        candidate_items: List[Dict],
        vector_similarities: List[float],
        ml_weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Calculate hybrid similarity scores combining vector similarity with weighted features.
        
        Args:
            query_item: Query/reference item dictionary
            candidate_items: List of candidate item dictionaries
            vector_similarities: List of vector similarity scores (from Pinecone)
            ml_weights: Optional ML weights dictionary. If None, uses global weights.
            
        Returns:
            List of tuples (item_dict, final_score) sorted by score descending
        """
        if len(candidate_items) != len(vector_similarities):
            raise ValueError("candidate_items and vector_similarities must have the same length")
        
        if ml_weights is None:
            ml_weights = ml_weights_service.get_all_weights()
        
        # Remove intercept from weights (not used in feature matching)
        feature_weights = {k: v for k, v in ml_weights.items() if k != "intercept"}
        
        results = []
        for item, vector_score in zip(candidate_items, vector_similarities):
            # Normalize vector score (Pinecone dot product is already normalized if embeddings are normalized)
            # Dot product of normalized vectors gives cosine similarity in range [-1, 1]
            # Normalize to [0, 1] for consistency
            normalized_vector_score = (vector_score + 1.0) / 2.0
            
            # Calculate weighted feature score (use empty dict if query_item is None)
            feature_score = 0.0
            if query_item:
                feature_score = self._calculate_weighted_features(
                    query_item,
                    item,
                    feature_weights
                )
            
            # Combine scores
            final_score = (
                self.vector_weight * normalized_vector_score +
                self.feature_weight * feature_score
            )
            
            results.append((item, final_score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results


# Global instance
similarity_service = SimilarityService()

