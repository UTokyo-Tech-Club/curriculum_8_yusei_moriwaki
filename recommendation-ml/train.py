#!/usr/bin/env python3
"""
Main training script for Mercari item similarity optimization.

Usage:
    python train.py                           # Use default config
    python train.py --config custom.yaml      # Use custom config
    python train.py --trials 200              # Override specific params
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_loader import MercariDataLoader
from optimizer import ItemSimilarityOptimizer
from utils import (
    get_experiment_id,
    load_config,
    print_config_summary,
    save_results,
    setup_logging,
    validate_config,
    format_time
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train item similarity model with hyperparameter optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default configuration
  python train.py

  # Use custom config file
  python train.py --config my_config.yaml

  # Override specific parameters
  python train.py --trials 200 --sample-limit 100000

  # Quick test run
  python train.py --trials 20 --sample-limit 10000

For more information, see README.md
        """
    )
    
    # Configuration
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    
    # Data parameters (override config)
    parser.add_argument(
        "--sample-limit",
        type=int,
        help="Number of records to load (overrides config)"
    )
    parser.add_argument(
        "--max-distance",
        type=int,
        help="Maximum sequence distance (overrides config)"
    )
    
    # Optimization parameters (override config)
    parser.add_argument(
        "--trials",
        type=int,
        help="Number of optimization trials (overrides config)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout in seconds (overrides config)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed (overrides config)"
    )
    
    # Output parameters
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (overrides config)"
    )
    parser.add_argument(
        "--experiment-id",
        type=str,
        help="Custom experiment ID (default: timestamp)"
    )
    
    return parser.parse_args()


def override_config(config, args):
    """Override config values with command line arguments."""
    if args.sample_limit is not None:
        config['data']['sample_limit'] = args.sample_limit
    
    if args.max_distance is not None:
        config['data']['max_sequence_distance'] = args.max_distance
    
    if args.trials is not None:
        config['optimization']['n_trials'] = args.trials
    
    if args.timeout is not None:
        config['optimization']['timeout'] = args.timeout
    
    if args.seed is not None:
        config['optimization']['random_seed'] = args.seed
    
    if args.log_level is not None:
        config['output']['log_level'] = args.log_level
    
    return config


def main():
    """Main training pipeline."""
    # Parse arguments
    args = parse_args()
    
    # Generate experiment ID
    experiment_id = args.experiment_id or get_experiment_id()
    
    try:
        # Load and validate configuration
        print(f"Loading configuration from: {args.config}")
        config = load_config(args.config)
        
        # Override with command line arguments
        config = override_config(config, args)
        
        # Validate configuration
        validate_config(config)
        
        # Setup logging
        logger = setup_logging(
            log_dir=config['output']['log_dir'],
            log_level=config['output']['log_level'],
            experiment_id=experiment_id
        )
        
        logger.info("=" * 80)
        logger.info("MERCARI ITEM SIMILARITY OPTIMIZATION")
        logger.info("=" * 80)
        logger.info(f"Experiment ID: {experiment_id}")
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print configuration
        print_config_summary(config, logger)
        
        start_time = datetime.now()
        
        # Step 1: Load data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: DATA LOADING")
        logger.info("=" * 80)
        
        data_loader = MercariDataLoader(
            sample_limit=config['data']['sample_limit'],
            dataset_name=config['data']['dataset_name'],
            logger=logger
        )
        
        data_loader.load_data()
        
        # Step 2: Generate training pairs
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: GENERATE TRAINING PAIRS")
        logger.info("=" * 80)
        
        pairs_df = data_loader.generate_training_pairs(
            decay_rate=config['model']['decay_rate'],
            max_distance=config['data']['max_sequence_distance'],
            sample_sessions=config['data'].get('sample_sessions'),
            min_session_length=config['data']['min_session_length']
        )
        
        # Step 3: Split data
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: SPLIT DATA")
        logger.info("=" * 80)
        
        X_train, X_val, y_train, y_val = data_loader.split_data(
            pairs_df,
            validation_split=config['optimization']['validation_split'],
            random_seed=config['optimization']['random_seed']
        )
        
        # Step 4: Optimize hyperparameters
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: HYPERPARAMETER OPTIMIZATION")
        logger.info("=" * 80)
        
        optimizer = ItemSimilarityOptimizer(
            feature_weights_config=config['model']['feature_weights'],
            n_trials=config['optimization']['n_trials'],
            timeout=config['optimization'].get('timeout'),
            random_seed=config['optimization']['random_seed'],
            logger=logger
        )
        
        best_params = optimizer.optimize(X_train, y_train, X_val, y_val)
        
        # Step 5: Evaluate
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: EVALUATION")
        logger.info("=" * 80)
        
        metrics = optimizer.evaluate(X_train, y_train, X_val, y_val, debug=True)
        feature_importance = optimizer.get_feature_importance()
        optimization_history = optimizer.get_optimization_history()
        
        # Generate diagnostic plots
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5b: GENERATING DIAGNOSTIC PLOTS")
        logger.info("=" * 80)
        
        try:
            plot_dir = Path(config['output']['results_dir']).parent / "plots"
            plot_dir.mkdir(exist_ok=True)
            
            # Save predictions vs targets plot
            plot_path = plot_dir / f"{experiment_id}_predictions.png"
            optimizer.plot_predictions_vs_targets(X_val, y_val, save_path=str(plot_path))
            
            # Save optimization history plot
            opt_plot_path = plot_dir / f"{experiment_id}_optimization.png"
            optimizer.plot_optimization_history(save_path=str(opt_plot_path))
            
        except Exception as e:
            logger.warning(f"Could not generate plots: {e}")
        
        # Step 6: Save results
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: SAVE RESULTS")
        logger.info("=" * 80)
        
        results = {
            "experiment_id": experiment_id,
            "config": config,
            "best_params": best_params,
            "metrics": metrics,
            "feature_importance": feature_importance,
            "optimization_history": optimization_history,
            "data_statistics": {
                "total_records": len(data_loader.data),
                "total_pairs": len(pairs_df),
                "train_samples": len(X_train),
                "val_samples": len(X_val),
            },
            "training_time_seconds": (datetime.now() - start_time).total_seconds(),
        }
        
        results_file = save_results(
            results,
            output_dir=config['output']['results_dir'],
            experiment_id=experiment_id,
            logger=logger
        )
        
        # Final summary
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Experiment ID: {experiment_id}")
        logger.info(f"Total time: {format_time(elapsed)}")
        logger.info(f"Results saved to: {results_file}")
        logger.info(f"Best validation MSE: {metrics['val_mse']:.6f}")
        logger.info(f"Best validation R²: {metrics['val_r2']:.6f}")
        logger.info("\nTop 3 most important features:")
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:3], 1):
            logger.info(f"  {i}. {feature}: {importance:.4f}")
        logger.info("=" * 80)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"\nMake sure the config file exists: {args.config}")
        print("You can copy config/config_example.yaml to config/config.yaml")
        return 1
        
    except Exception as e:
        print(f"Error during training: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

