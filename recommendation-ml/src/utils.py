"""
Utility functions for configuration, logging, and result management.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Dictionary containing configuration
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required sections
    required_sections = ['data', 'model', 'optimization', 'output']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section in config: {section}")
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate data section
    data = config.get('data', {})
    if data.get('sample_limit', 0) <= 0:
        raise ValueError("data.sample_limit must be positive")
    
    # Validate model section
    model = config.get('model', {})
    if not 0 < model.get('decay_rate', 0) <= 1:
        raise ValueError("model.decay_rate must be between 0 and 1")
    
    # Validate optimization section
    opt = config.get('optimization', {})
    if opt.get('n_trials', 0) <= 0:
        raise ValueError("optimization.n_trials must be positive")
    if not 0 < opt.get('validation_split', 0) < 1:
        raise ValueError("optimization.validation_split must be between 0 and 1")


def setup_logging(
    log_dir: str = "results/logs",
    log_level: str = "INFO",
    experiment_id: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_dir: Directory to save log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        experiment_id: Unique experiment identifier
        
    Returns:
        Configured logger instance
    """
    # Create log directory if not exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate experiment ID if not provided
    if experiment_id is None:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configure logger
    logger = logging.getLogger("recommendation_ml")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = Path(log_dir) / f"{experiment_id}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger


def save_results(
    results: Dict[str, Any],
    output_dir: str = "results/models",
    experiment_id: Optional[str] = None,
    logger: Optional[logging.Logger] = None
) -> str:
    """
    Save optimization results to JSON file.
    
    Args:
        results: Dictionary containing results
        output_dir: Directory to save results
        experiment_id: Unique experiment identifier
        logger: Logger instance
        
    Returns:
        Path to saved results file
    """
    # Create output directory if not exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate experiment ID if not provided
    if experiment_id is None:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Add metadata
    results['experiment_id'] = experiment_id
    results['saved_at'] = datetime.now().isoformat()
    
    # Save to JSON
    output_file = Path(output_dir) / f"{experiment_id}_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    if logger:
        logger.info(f"Results saved to: {output_file}")
    
    return str(output_file)


def load_results(results_path: str) -> Dict[str, Any]:
    """
    Load results from JSON file.
    
    Args:
        results_path: Path to results file
        
    Returns:
        Dictionary containing results
    """
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    return results


def get_experiment_id() -> str:
    """
    Generate a unique experiment ID based on timestamp.
    
    Returns:
        Experiment ID string (format: YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_config_summary(config: Dict[str, Any], logger: Optional[logging.Logger] = None) -> None:
    """
    Print a summary of the configuration.
    
    Args:
        config: Configuration dictionary
        logger: Logger instance (if None, uses print)
    """
    log_func = logger.info if logger else print
    
    log_func("=" * 80)
    log_func("CONFIGURATION SUMMARY")
    log_func("=" * 80)
    
    log_func("\nData Parameters:")
    for key, value in config.get('data', {}).items():
        log_func(f"  {key}: {value}")
    
    log_func("\nModel Parameters:")
    for key, value in config.get('model', {}).items():
        if key == 'feature_weights':
            log_func(f"  {key}:")
            for feat, range_val in value.items():
                log_func(f"    {feat}: {range_val}")
        else:
            log_func(f"  {key}: {value}")
    
    log_func("\nOptimization Parameters:")
    for key, value in config.get('optimization', {}).items():
        log_func(f"  {key}: {value}")
    
    log_func("\nOutput Settings:")
    for key, value in config.get('output', {}).items():
        log_func(f"  {key}: {value}")
    
    log_func("=" * 80)


def format_time(seconds: float) -> str:
    """
    Format seconds into human-readable time string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_results_files(results_dir: str = "results/models") -> list:
    """
    Get list of all result files in the directory.
    
    Args:
        results_dir: Directory containing result files
        
    Returns:
        List of result file paths
    """
    results_path = Path(results_dir)
    if not results_path.exists():
        return []
    
    return sorted(results_path.glob("*_results.json"), reverse=True)



