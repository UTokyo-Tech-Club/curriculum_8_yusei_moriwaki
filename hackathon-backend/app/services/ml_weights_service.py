"""
ML Weights Service - Loads and provides optimized feature weights from ML training results.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class MLWeightsService:
    """Service for loading and providing ML-optimized feature weights."""
    
    def __init__(self):
        self.weights: Optional[Dict[str, float]] = None
        self._load_weights()
    
    def _load_weights(self) -> None:
        """Load weights from the configured ML results JSON file."""
        weights_path = settings.ML_WEIGHTS_PATH
        
        if not weights_path:
            # Try to find the most recent results file
            ml_dir = Path(__file__).parent.parent.parent.parent / "recommendation-ml" / "results" / "models"
            if ml_dir.exists():
                result_files = sorted(ml_dir.glob("*_results.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                if result_files:
                    weights_path = str(result_files[0])
                    logger.info(f"Auto-detected ML weights file: {weights_path}")
        
        if not weights_path:
            logger.warning("No ML weights path configured and no auto-detected file found. Using default weights.")
            self.weights = self._get_default_weights()
            return
        
        weights_path = Path(weights_path)
        if not weights_path.exists():
            logger.warning(f"ML weights file not found: {weights_path}. Using default weights.")
            self.weights = self._get_default_weights()
            return
        
        try:
            with open(weights_path, 'r') as f:
                data = json.load(f)
                self.weights = data.get('best_params', {})
                
                if not self.weights:
                    logger.warning("No 'best_params' found in ML results file. Using default weights.")
                    self.weights = self._get_default_weights()
                else:
                    logger.info(f"Loaded ML weights from {weights_path}")
                    logger.info(f"Loaded {len(self.weights)} feature weights")
        except Exception as e:
            logger.error(f"Error loading ML weights from {weights_path}: {e}. Using default weights.")
            self.weights = self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Return default weights if ML weights cannot be loaded."""
        return {
            "c0": 0.5,
            "c1": 0.3,
            "c2": 0.4,
            "brand": 0.7,
            "condition": 0.3,
            "size": 0.4,
            "match_count": 0.6,
            "category_hierarchy_score": 0.3,
            "both_have_size": 0.1,
            "seq_distance_log": 0.4,
            "seq_dist_x_category": 0.5,
            "seq_dist_x_brand": 0.7,
            "intercept": 0.0
        }
    
    def get_feature_weight(self, feature_name: str) -> float:
        """
        Get the weight for a specific feature.
        
        Args:
            feature_name: Name of the feature (e.g., 'c0', 'brand', 'condition')
            
        Returns:
            Weight value for the feature, or 0.0 if not found
        """
        if not self.weights:
            return 0.0
        return self.weights.get(feature_name, 0.0)
    
    def get_all_weights(self) -> Dict[str, float]:
        """
        Get all feature weights.
        
        Returns:
            Dictionary mapping feature names to weights
        """
        return self.weights.copy() if self.weights else {}
    
    def reload_weights(self, weights_path: Optional[str] = None) -> None:
        """
        Reload weights from a file.
        
        Args:
            weights_path: Optional path to weights file. If None, uses configured path.
        """
        if weights_path:
            settings.ML_WEIGHTS_PATH = weights_path
        self._load_weights()


# Global instance
ml_weights_service = MLWeightsService()

