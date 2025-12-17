"""
Item similarity optimizer using Optuna for hyperparameter tuning.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score


class ItemSimilarityOptimizer:
    """
    Optimizes feature weights for item similarity calculation.
    """
    
    def __init__(
        self,
        feature_weights_config: Dict[str, List[float]],
        n_trials: int = 100,
        timeout: Optional[int] = None,
        random_seed: int = 42,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the optimizer.
        
        Args:
            feature_weights_config: Dictionary mapping feature names to [min, max] ranges
            n_trials: Number of optimization trials
            timeout: Timeout in seconds (None = no timeout)
            random_seed: Random seed for reproducibility
            logger: Logger instance
        """
        self.feature_weights_config = feature_weights_config
        self.n_trials = n_trials
        self.timeout = timeout
        self.random_seed = random_seed
        self.logger = logger or logging.getLogger(__name__)
        
        self.study = None
        self.best_params = None
        self.optimization_history = []
        
    def calculate_similarity(
        self,
        features: pd.DataFrame,
        params: Dict[str, float]
    ) -> np.ndarray:
        """
        Calculate similarity scores using weighted features.
        
        IMPROVED MODEL v2:
        - Uses normalized weighted sum with INTERCEPT
        - Intercept resolves systematic bias issue
        - More stable and interpretable
        
        Args:
            features: DataFrame with feature columns
            params: Dictionary of feature weights (including 'intercept')
            
        Returns:
            Array of similarity scores (0-1)
        """
        # Extract intercept (baseline similarity)
        intercept = params.get('intercept', 0.0)
        
        # Calculate weighted sum of features
        score = np.zeros(len(features))
        total_weight = 0.0
        
        for feature_name, weight in params.items():
            if feature_name == 'intercept':
                continue  # Skip intercept in feature loop
                
            feature_col = f"{feature_name}_match"
            if feature_col in features.columns:
                score += weight * features[feature_col].values
                total_weight += weight
        
        # Normalize by total weight to get expected value (0-1)
        if total_weight > 0:
            normalized_score = score / total_weight
        else:
            normalized_score = np.zeros(len(features))
        
        # Add intercept (baseline similarity when no features match)
        similarity = normalized_score + intercept
        
        # Clip to ensure values are in [0, 1] range
        similarity = np.clip(similarity, 0.0, 1.0)
        
        return similarity
    
    def objective(
        self,
        trial: optuna.Trial,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> float:
        """
        Objective function for Optuna optimization.
        
        Args:
            trial: Optuna trial object
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            
        Returns:
            Validation MSE (to be minimized)
        """
        # Suggest hyperparameters
        params = {}
        for feature_name, (min_val, max_val) in self.feature_weights_config.items():
            if feature_name == 'intercept':
                # Intercept can be negative (to handle systematic bias)
                params[feature_name] = trial.suggest_float(
                    "intercept",
                    min_val,
                    max_val
                )
            else:
                params[feature_name] = trial.suggest_float(
                    f"w_{feature_name}",
                    min_val,
                    max_val
                )
        
        # Calculate predictions on validation set
        y_pred_val = self.calculate_similarity(X_val, params)
        val_mse = mean_squared_error(y_val, y_pred_val)
        
        # Also calculate training MSE for monitoring
        y_pred_train = self.calculate_similarity(X_train, params)
        train_mse = mean_squared_error(y_train, y_pred_train)
        
        # Store metrics in trial user attributes
        trial.set_user_attr("train_mse", train_mse)
        trial.set_user_attr("val_mse", val_mse)
        
        return val_mse
    
    def optimize(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series
    ) -> Dict[str, float]:
        """
        Run hyperparameter optimization.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            
        Returns:
            Dictionary of best parameters
        """
        self.logger.info("\n" + "=" * 80)
        self.logger.info("STARTING HYPERPARAMETER OPTIMIZATION")
        self.logger.info("=" * 80)
        self.logger.info(f"Number of trials: {self.n_trials}")
        self.logger.info(f"Timeout: {self.timeout if self.timeout else 'None'}")
        self.logger.info(f"Random seed: {self.random_seed}")
        
        start_time = datetime.now()
        
        # Create Optuna study
        self.study = optuna.create_study(
            direction="minimize",
            study_name="item_similarity_optimization",
            sampler=optuna.samplers.TPESampler(seed=self.random_seed)
        )
        
        # Run optimization
        self.logger.info("\nRunning optimization...")
        self.study.optimize(
            lambda trial: self.objective(trial, X_train, y_train, X_val, y_val),
            n_trials=self.n_trials,
            timeout=self.timeout,
            show_progress_bar=True
        )
        
        # Extract best parameters
        self.best_params = {
            key.replace("w_", ""): value
            for key, value in self.study.best_params.items()
        }
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("OPTIMIZATION COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Best validation MSE: {self.study.best_value:.6f}")
        self.logger.info(f"Number of trials completed: {len(self.study.trials)}")
        self.logger.info(f"Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        
        # Log best parameters
        self.logger.info("\nBest Parameters:")
        for param, value in sorted(self.best_params.items(), key=lambda x: x[1], reverse=True):
            self.logger.info(f"  w_{param}: {value:.4f}")
        
        return self.best_params
    
    def evaluate(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        debug: bool = False
    ) -> Dict[str, float]:
        """
        Evaluate the best model on train and validation sets.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            debug: If True, print additional debugging information
            
        Returns:
            Dictionary of evaluation metrics
        """
        if self.best_params is None:
            raise ValueError("Optimization not run yet. Call optimize() first.")
        
        # Predictions
        y_pred_train = self.calculate_similarity(X_train, self.best_params)
        y_pred_val = self.calculate_similarity(X_val, self.best_params)
        
        # Calculate metrics
        metrics = {
            "train_mse": mean_squared_error(y_train, y_pred_train),
            "train_r2": r2_score(y_train, y_pred_train),
            "val_mse": mean_squared_error(y_val, y_pred_val),
            "val_r2": r2_score(y_val, y_pred_val),
        }
        
        # Additional debugging metrics
        if debug:
            metrics["train_pred_mean"] = float(y_pred_train.mean())
            metrics["train_pred_std"] = float(y_pred_train.std())
            metrics["train_target_mean"] = float(y_train.mean())
            metrics["train_target_std"] = float(y_train.std())
            metrics["val_pred_mean"] = float(y_pred_val.mean())
            metrics["val_pred_std"] = float(y_pred_val.std())
            metrics["val_target_mean"] = float(y_val.mean())
            metrics["val_target_std"] = float(y_val.std())
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("EVALUATION RESULTS")
        self.logger.info("=" * 80)
        self.logger.info(f"Training:")
        self.logger.info(f"  MSE: {metrics['train_mse']:.6f}")
        self.logger.info(f"  R²:  {metrics['train_r2']:.6f}")
        self.logger.info(f"\nValidation:")
        self.logger.info(f"  MSE: {metrics['val_mse']:.6f}")
        self.logger.info(f"  R²:  {metrics['val_r2']:.6f}")
        
        if debug:
            self.logger.info(f"\nDebug Statistics:")
            self.logger.info(f"  Train predictions: mean={metrics['train_pred_mean']:.4f}, std={metrics['train_pred_std']:.4f}")
            self.logger.info(f"  Train targets: mean={metrics['train_target_mean']:.4f}, std={metrics['train_target_std']:.4f}")
            self.logger.info(f"  Val predictions: mean={metrics['val_pred_mean']:.4f}, std={metrics['val_pred_std']:.4f}")
            self.logger.info(f"  Val targets: mean={metrics['val_target_mean']:.4f}, std={metrics['val_target_std']:.4f}")
        
        return metrics
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance based on optimized weights.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.best_params is None:
            raise ValueError("Optimization not run yet. Call optimize() first.")
        
        # Exclude intercept from importance calculation
        feature_params = {k: v for k, v in self.best_params.items() if k != 'intercept'}
        
        # Normalize weights to sum to 1 for importance interpretation
        total_weight = sum(abs(w) for w in feature_params.values())
        
        if total_weight == 0:
            importance = {k: 0.0 for k in feature_params.keys()}
        else:
            importance = {
                k: abs(v) / total_weight
                for k, v in feature_params.items()
            }
        
        # Sort by importance
        importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("FEATURE IMPORTANCE")
        self.logger.info("=" * 80)
        
        for feature, score in importance.items():
            bar_length = int(score * 50)
            bar = "█" * bar_length
            self.logger.info(f"  {feature:12s}: {score:6.4f} {bar}")
        
        return importance
    
    def get_optimization_history(self) -> List[Dict[str, float]]:
        """
        Get optimization history (all trials).
        
        Returns:
            List of dictionaries with trial information
        """
        if self.study is None:
            return []
        
        history = []
        for trial in self.study.trials:
            trial_info = {
                "trial_number": trial.number,
                "value": trial.value,
                "params": trial.params,
                "state": trial.state.name,
            }
            
            # Add user attributes if available
            if trial.user_attrs:
                trial_info.update(trial.user_attrs)
            
            history.append(trial_info)
        
        return history
    
    def plot_optimization_history(self, save_path: Optional[str] = None) -> None:
        """
        Plot optimization history (requires matplotlib).
        
        Args:
            save_path: If provided, save plot to this path instead of showing
        """
        if self.study is None:
            self.logger.warning("No optimization run yet.")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            # Get trial values
            trials = [t.number for t in self.study.trials]
            values = [t.value for t in self.study.trials]
            
            # Plot
            plt.figure(figsize=(10, 6))
            plt.plot(trials, values, 'b-', alpha=0.6, label='Trial MSE')
            plt.plot(trials, [min(values[:i+1]) for i in range(len(values))],
                    'r-', linewidth=2, label='Best MSE')
            plt.xlabel('Trial')
            plt.ylabel('Validation MSE')
            plt.title('Optimization History')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                self.logger.info(f"Plot saved to: {save_path}")
            else:
                plt.show()
            plt.close()
            
        except ImportError:
            self.logger.warning("matplotlib not available for plotting")
    
    def plot_predictions_vs_targets(
        self,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        save_path: Optional[str] = None
    ) -> None:
        """
        Plot predicted vs target values for debugging.
        
        Args:
            X_val: Validation features
            y_val: Validation targets
            save_path: If provided, save plot to this path instead of showing
        """
        if self.best_params is None:
            self.logger.warning("Optimization not run yet.")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            # Get predictions
            y_pred = self.calculate_similarity(X_val, self.best_params)
            
            # Create figure with multiple subplots
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # 1. Scatter plot: Predicted vs Target
            ax1 = axes[0, 0]
            ax1.scatter(y_val, y_pred, alpha=0.3, s=10)
            ax1.plot([0, 1], [0, 1], 'r--', linewidth=2, label='Perfect prediction')
            ax1.set_xlabel('Target')
            ax1.set_ylabel('Predicted')
            ax1.set_title('Predictions vs Targets')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. Distribution of targets
            ax2 = axes[0, 1]
            ax2.hist(y_val, bins=50, alpha=0.7, color='blue', edgecolor='black')
            ax2.axvline(y_val.mean(), color='red', linestyle='--', linewidth=2, 
                       label=f'Mean: {y_val.mean():.3f}')
            ax2.set_xlabel('Target Value')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Distribution of Targets')
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. Distribution of predictions
            ax3 = axes[1, 0]
            ax3.hist(y_pred, bins=50, alpha=0.7, color='green', edgecolor='black')
            ax3.axvline(y_pred.mean(), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {y_pred.mean():.3f}')
            ax3.set_xlabel('Predicted Value')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Distribution of Predictions')
            ax3.legend()
            ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. Residuals
            ax4 = axes[1, 1]
            residuals = y_val - y_pred
            ax4.scatter(y_pred, residuals, alpha=0.3, s=10)
            ax4.axhline(0, color='red', linestyle='--', linewidth=2)
            ax4.set_xlabel('Predicted')
            ax4.set_ylabel('Residual (Target - Predicted)')
            ax4.set_title(f'Residuals (Mean: {residuals.mean():.4f}, Std: {residuals.std():.4f})')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                self.logger.info(f"Plot saved to: {save_path}")
            else:
                plt.show()
            plt.close()
            
        except ImportError:
            self.logger.warning("matplotlib not available for plotting")

