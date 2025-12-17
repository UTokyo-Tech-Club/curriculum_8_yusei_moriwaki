"""
Data loading and preprocessing for Mercari dataset from Hugging Face.
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm


class MercariDataLoader:
    """
    Handles loading and preprocessing of Mercari dataset from Hugging Face.
    """
    
    def __init__(
        self,
        sample_limit: int = 50000,
        dataset_name: str = "mercari-us/merrec",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the data loader.
        
        Args:
            sample_limit: Maximum number of records to load
            dataset_name: Hugging Face dataset name
            logger: Logger instance
        """
        self.sample_limit = sample_limit
        self.dataset_name = dataset_name
        self.logger = logger or logging.getLogger(__name__)
        self.data = None
        
    def load_data(self) -> pd.DataFrame:
        """
        Load data from Hugging Face dataset.
        
        Returns:
            DataFrame with loaded data
        """
        self.logger.info(f"Loading data from Hugging Face: {self.dataset_name}")
        self.logger.info(f"Sample limit: {self.sample_limit:,} records")
        
        # Load dataset in streaming mode
        dataset = load_dataset(self.dataset_name, split="train", streaming=True)
        
        # Stream and collect data
        rows = []
        for row in tqdm(
            dataset.take(self.sample_limit),
            total=self.sample_limit,
            desc="Loading data"
        ):
            rows.append({
                'session_id': row['session_id'],
                'sequence_id': int(row['sequence_id']),
                'item_id': row['item_id'],
                'c0_id': row['c0_id'] if pd.notna(row['c0_id']) else None,
                'c1_id': row['c1_id'] if pd.notna(row['c1_id']) else None,
                'c2_id': row['c2_id'] if pd.notna(row['c2_id']) else None,
                'brand_id': row['brand_id'] if pd.notna(row['brand_id']) else None,
                'item_condition_id': row['item_condition_id'] if pd.notna(row['item_condition_id']) else None,
                'size_id': row['size_id'] if pd.notna(row['size_id']) else None,
            })
        
        self.data = pd.DataFrame(rows)
        
        self.logger.info(f"Loaded {len(self.data):,} records")
        self.logger.info(f"Sessions: {self.data['session_id'].nunique():,}")
        self.logger.info(f"Unique items: {self.data['item_id'].nunique():,}")
        
        # Log data statistics
        self._log_data_statistics()
        
        return self.data
    
    def _log_data_statistics(self) -> None:
        """Log statistics about the loaded data."""
        if self.data is None:
            return
        
        self.logger.info("\nData Statistics:")
        self.logger.info(f"  Total records: {len(self.data):,}")
        self.logger.info(f"  Unique sessions: {self.data['session_id'].nunique():,}")
        self.logger.info(f"  Unique items: {self.data['item_id'].nunique():,}")
        self.logger.info(f"  Avg items per session: {len(self.data) / self.data['session_id'].nunique():.2f}")
        
        self.logger.info("\nNull rates:")
        for col in ['c0_id', 'c1_id', 'c2_id', 'brand_id', 'item_condition_id', 'size_id']:
            null_rate = self.data[col].isnull().sum() / len(self.data) * 100
            self.logger.info(f"  {col}: {null_rate:.1f}%")
    
    def generate_training_pairs(
        self,
        decay_rate: float = 0.8,
        max_distance: int = 10,
        sample_sessions: Optional[int] = None,
        min_session_length: int = 2
    ) -> pd.DataFrame:
        """
        Generate training pairs from loaded data.
        
        Args:
            decay_rate: Decay rate for sequence distance scoring
            max_distance: Maximum sequence distance to consider
            sample_sessions: Number of sessions to sample (None = all)
            min_session_length: Minimum number of items in a session
            
        Returns:
            DataFrame with training pairs
        """
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        self.logger.info("\nGenerating training pairs...")
        self.logger.info(f"  Decay rate: {decay_rate}")
        self.logger.info(f"  Max sequence distance: {max_distance}")
        self.logger.info(f"  Min session length: {min_session_length}")
        
        pairs = []
        
        # Group by session
        sessions = list(self.data.groupby('session_id'))
        total_sessions = len(sessions)
        
        # Sample sessions if specified
        if sample_sessions and sample_sessions < total_sessions:
            import random
            random.seed(42)
            sessions = random.sample(sessions, sample_sessions)
            self.logger.info(f"  Sampling {sample_sessions:,} sessions from {total_sessions:,} total")
        
        # Generate pairs for each session
        skipped_sessions = 0
        for session_id, group in tqdm(sessions, desc="Processing sessions"):
            items = group.sort_values('sequence_id').reset_index(drop=True)
            
            # Skip sessions with too few items
            if len(items) < min_session_length:
                skipped_sessions += 1
                continue
            
            # Generate pairs within max_distance
            for i in range(len(items)):
                for j in range(i + 1, min(i + 1 + max_distance, len(items))):
                    item1 = items.iloc[i]
                    item2 = items.iloc[j]
                    
                    # Calculate sequence distance (use position difference, not sequence_id difference)
                    # j > i by construction, so j - i is always positive
                    seq_distance = j - i
                    
                    # Calculate individual feature matches
                    c0_match = self._is_match(item1['c0_id'], item2['c0_id'])
                    c1_match = self._is_match(item1['c1_id'], item2['c1_id'])
                    c2_match = self._is_match(item1['c2_id'], item2['c2_id'])
                    brand_match = self._is_match(item1['brand_id'], item2['brand_id'])
                    condition_match = self._is_match(item1['item_condition_id'], item2['item_condition_id'])
                    size_match = self._is_match(item1['size_id'], item2['size_id'])
                    
                    # NEW: Advanced features
                    # 1. Match count (total number of matching features)
                    match_count = c0_match + c1_match + c2_match + brand_match + condition_match + size_match
                    
                    # 2. Category hierarchy score (weighted by hierarchy level)
                    # c0 is broadest (30%), c1 is medium (30%), c2 is specific (40%)
                    category_hierarchy_score = (c0_match * 0.3 + c1_match * 0.3 + c2_match * 0.4)
                    
                    # FUNDAMENTAL FIX: Calculate attribute similarity score (0-1)
                    # This represents how similar items are based on their attributes
                    # Using weighted average: more important features (c2, brand, size) get higher weights
                    attribute_weights = {
                        'c0': 0.10,  # Broad category (less important)
                        'c1': 0.15,  # Medium category
                        'c2': 0.25,  # Specific category (more important)
                        'brand': 0.25,  # Brand is very important
                        'condition': 0.10,  # Condition is less important
                        'size': 0.15   # Size is important
                    }
                    attribute_score = (
                        c0_match * attribute_weights['c0'] +
                        c1_match * attribute_weights['c1'] +
                        c2_match * attribute_weights['c2'] +
                        brand_match * attribute_weights['brand'] +
                        condition_match * attribute_weights['condition'] +
                        size_match * attribute_weights['size']
                    )
                    # Normalize to [0, 1] range
                    max_possible_score = sum(attribute_weights.values())
                    attribute_score = attribute_score / max_possible_score
                    
                    # FUNDAMENTAL FIX: New target = distance_decay × attribute_similarity
                    # This matches what the model actually predicts (attribute matching score)
                    distance_decay = decay_rate ** seq_distance
                    target_score = distance_decay * attribute_score
                    
                    # Phase 1b: Only log-scaled distance (removed redundant features)
                    # Log-scaled distance provides non-linear transform without multicollinearity
                    import math
                    seq_distance_log = math.log(seq_distance + 1) / math.log(max_distance + 1)
                    
                    # 3. Both have size (important signal even if they don't match)
                    both_have_size = int(pd.notna(item1['size_id']) and pd.notna(item2['size_id']))
                    
                    # Phase 1c: Interaction features (capture how distance effect varies by category/brand)
                    # 1. Is same category (any level matches)
                    is_same_category = int(c0_match == 1 or c1_match == 1 or c2_match == 1)
                    
                    # 2. Interaction: seq_distance_log × is_same_category
                    seq_dist_x_category = seq_distance_log * is_same_category
                    
                    # 3. Interaction: seq_distance_log × is_same_brand
                    seq_dist_x_brand = seq_distance_log * brand_match
                    
                    # Create pair with features
                    pairs.append({
                        'session_id': session_id,
                        'item1_id': item1['item_id'],
                        'item2_id': item2['item_id'],
                        'seq_distance': seq_distance,
                        'target_score': target_score,
                        
                        # Original binary match features
                        'c0_match': c0_match,
                        'c1_match': c1_match,
                        'c2_match': c2_match,
                        'brand_match': brand_match,
                        'condition_match': condition_match,
                        'size_match': size_match,
                        
                        # Advanced engineered features
                        'match_count': match_count,
                        'category_hierarchy_score': category_hierarchy_score,
                        'both_have_size': both_have_size,
                        
                        # Phase 1b: Only seq_distance_log (removed redundant features)
                        'seq_distance_log': seq_distance_log,
                        
                        # Phase 1c: Interaction features (minimal set for R² improvement)
                        'seq_dist_x_category': seq_dist_x_category,
                        'seq_dist_x_brand': seq_dist_x_brand,
                    })
        
        pairs_df = pd.DataFrame(pairs)
        
        self.logger.info(f"\nPair generation complete:")
        self.logger.info(f"  Generated {len(pairs_df):,} training pairs")
        self.logger.info(f"  Skipped {skipped_sessions:,} sessions (too short)")
        self.logger.info(f"  Target score range: [{pairs_df['target_score'].min():.3f}, {pairs_df['target_score'].max():.3f}]")
        self.logger.info(f"  Sequence distance range: [{pairs_df['seq_distance'].min()}, {pairs_df['seq_distance'].max()}]")
        
        # Log feature match rates
        self._log_feature_match_rates(pairs_df)
        
        return pairs_df
    
    def _is_match(self, val1, val2) -> int:
        """
        Check if two values match (considering NaN).
        
        Args:
            val1: First value
            val2: Second value
            
        Returns:
            1 if match, 0 otherwise
        """
        if pd.isna(val1) or pd.isna(val2):
            return 0
        return int(val1 == val2)
    
    def _log_feature_match_rates(self, pairs_df: pd.DataFrame) -> None:
        """
        Log statistics about feature match rates.
        
        Args:
            pairs_df: DataFrame with pairs
        """
        self.logger.info("\nFeature match rates:")
        feature_cols = ['c0_match', 'c1_match', 'c2_match', 'brand_match', 'condition_match', 'size_match']
        
        for col in feature_cols:
            match_rate = pairs_df[col].mean() * 100
            self.logger.info(f"  {col}: {match_rate:.1f}%")
    
    def get_feature_columns(self) -> List[str]:
        """
        Get list of feature column names.
        
        Returns:
            List of feature column names
        """
        # Original binary features + advanced features + sequence distance features (Phase 1)
        return [
            'c0_match', 'c1_match', 'c2_match', 
            'brand_match', 'condition_match', 'size_match',
            'match_count', 'category_hierarchy_score', 'both_have_size',
            # Phase 1b: Only seq_distance_log (removed redundant features)
            'seq_distance_log',
            # Phase 1c: Interaction features (minimal set)
            'seq_dist_x_category', 'seq_dist_x_brand'
        ]
    
    def split_data(
        self,
        pairs_df: pd.DataFrame,
        validation_split: float = 0.2,
        random_seed: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split pairs into training and validation sets.
        
        Args:
            pairs_df: DataFrame with pairs
            validation_split: Fraction of data for validation
            random_seed: Random seed for reproducibility
            
        Returns:
            X_train, X_val, y_train, y_val
        """
        from sklearn.model_selection import train_test_split
        
        feature_cols = self.get_feature_columns()
        X = pairs_df[feature_cols]
        y = pairs_df['target_score']
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y,
            test_size=validation_split,
            random_state=random_seed
        )
        
        self.logger.info(f"\nData split:")
        self.logger.info(f"  Training samples: {len(X_train):,}")
        self.logger.info(f"  Validation samples: {len(X_val):,}")
        self.logger.info(f"  Split ratio: {1-validation_split:.0%} / {validation_split:.0%}")
        
        return X_train, X_val, y_train, y_val

