# Mercari Item Similarity Optimization

Machine learning optimization for item similarity hyperparameters using the Mercari recommendation dataset from Hugging Face.

## Overview

This project optimizes feature weights for calculating item similarity in a recommendation system. It uses session-based user behavior data to learn which item attributes (category, brand, size, etc.) are most important for predicting item co-occurrence within sessions.

### Key Features

- **Hugging Face Integration**: Direct streaming from `mercari-us/merrec` dataset
- **Configurable Parameters**: YAML-based configuration for all hyperparameters
- **Optuna Optimization**: State-of-the-art hyperparameter tuning
- **Comprehensive Logging**: Detailed logs with timestamps for experiment tracking
- **Result Management**: JSON-based result storage with full reproducibility
- **Analysis Tools**: Jupyter notebook for visualizing results

## Project Structure

```
recommendation-ml/
├── config/
│   ├── config.yaml              # Main configuration file
│   └── config_example.yaml      # Example with detailed comments
├── src/
│   ├── __init__.py
│   ├── data_loader.py           # Hugging Face data loading
│   ├── optimizer.py             # Optuna optimization
│   └── utils.py                 # Helper functions
├── results/
│   ├── logs/                    # Training logs (timestamped)
│   └── models/                  # Saved parameters (JSON)
├── notebooks/
│   └── analysis.ipynb           # Results analysis
├── requirements.txt
├── README.md
└── train.py                     # Main entry point
```

## Installation

### 1. Create Virtual Environment

```bash
cd recommendation-ml
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python train.py --help
```

## Quick Start

### Basic Usage

```bash
# Use default configuration
python train.py

# View all options
python train.py --help
```

### Quick Test Run (5-10 minutes)

```bash
python train.py --trials 20 --sample-limit 10000
```

### Full Training Run (30-60 minutes)

```bash
python train.py --trials 200 --sample-limit 100000
```

## Configuration

### Using Config Files

Edit `config/config.yaml` to adjust parameters:

```yaml
data:
  sample_limit: 50000              # Number of records to load
  max_sequence_distance: 10         # Max distance for pair generation
  
model:
  decay_rate: 0.8                  # Sequence distance decay rate
  
optimization:
  n_trials: 100                    # Number of optimization trials
  validation_split: 0.2            # Validation set size
```

See `config/config_example.yaml` for detailed parameter explanations.

### Command Line Overrides

Override config parameters from command line:

```bash
# Override number of trials
python train.py --trials 200

# Override sample limit and max distance
python train.py --sample-limit 100000 --max-distance 15

# Override multiple parameters
python train.py --trials 50 --sample-limit 20000 --seed 123
```

## Parameters Guide

### Data Parameters

- **sample_limit**: Number of records to load from Hugging Face
  - Small (10,000): Quick tests (~5 min)
  - Medium (50,000): Balanced (~20 min)
  - Large (200,000): Production (~60 min)

- **max_sequence_distance**: Maximum sequence gap for item pairs
  - Lower (5): Fewer pairs, faster, focuses on nearby items
  - Higher (15): More pairs, slower, captures broader patterns

### Model Parameters

- **decay_rate**: How quickly similarity decays with distance
  - 0.9: Slow decay (distant items still related)
  - 0.8: Medium decay (recommended)
  - 0.7: Fast decay (only close items matter)

### Optimization Parameters

- **n_trials**: Number of Optuna optimization trials
  - Quick test: 20-50
  - Standard: 100-200
  - Thorough: 500+

- **validation_split**: Fraction of data for validation
  - Recommended: 0.2 (80% train, 20% validation)

## Usage Examples

### Example 1: Quick Experimentation

```bash
python train.py \
  --trials 30 \
  --sample-limit 10000 \
  --max-distance 5
```

### Example 2: Standard Training

```bash
python train.py \
  --config config/config.yaml \
  --trials 100
```

### Example 3: Production Run

```bash
python train.py \
  --trials 500 \
  --sample-limit 200000 \
  --max-distance 15 \
  --timeout 7200
```

### Example 4: Custom Experiment ID

```bash
python train.py \
  --experiment-id my_experiment_v1 \
  --trials 100
```

## Understanding Results

### Output Files

After training, you'll find:

1. **Results JSON** (`results/models/{experiment_id}_results.json`):
   - Best hyperparameters
   - Performance metrics (MSE, R²)
   - Feature importance
   - Full optimization history

2. **Log File** (`results/logs/{experiment_id}.log`):
   - Detailed execution log
   - Progress updates
   - Error messages

### Key Metrics

- **MSE (Mean Squared Error)**: Lower is better
  - Good: < 0.05
  - Excellent: < 0.02

- **R² Score**: Higher is better (0-1 range)
  - Good: > 0.7
  - Excellent: > 0.85

### Feature Importance

The optimizer learns which features are most important:

```
Feature Importance:
  c1          : 0.3542 ████████████████████
  brand       : 0.2817 ███████████████
  c2          : 0.1893 ██████████
  c0          : 0.1248 ██████
  condition   : 0.0345 ██
  size        : 0.0155 █
```

This tells you which attributes drive item similarity in your dataset.

## Advanced Usage

### Analyzing Results

Use the provided Jupyter notebook:

```bash
jupyter notebook notebooks/analysis.ipynb
```

The notebook provides:
- Optimization history visualization
- Feature importance comparison
- Multiple experiment comparison
- Performance metric plots

### Loading Saved Results

```python
from src.utils import load_results

# Load specific experiment
results = load_results('results/models/20250116_143022_results.json')

# Access best parameters
best_params = results['best_params']
print(f"Best C1 weight: {best_params['c1']}")

# Access metrics
metrics = results['metrics']
print(f"Validation R²: {metrics['val_r2']:.4f}")
```

### Using Optimized Parameters

```python
# In your recommendation system
from src.optimizer import ItemSimilarityOptimizer

optimizer = ItemSimilarityOptimizer(...)
# Load your optimized parameters
optimizer.best_params = best_params

# Calculate similarity for new items
similarity_score = optimizer.calculate_similarity(features, best_params)
```

## Troubleshooting

### Out of Memory

If you run out of memory:

1. Reduce `sample_limit`
2. Reduce `max_sequence_distance`
3. Use `sample_sessions` to limit sessions

```bash
python train.py --sample-limit 20000 --max-distance 5
```

### Slow Training

If training is too slow:

1. Reduce `n_trials`
2. Add a timeout
3. Use smaller dataset

```bash
python train.py --trials 50 --timeout 1800
```

### Configuration Errors

If config file has errors:

1. Check YAML syntax (indentation, colons)
2. Validate parameter ranges
3. Use `config_example.yaml` as reference

## Performance Tips

1. **Start Small**: Test with small parameters first
2. **Monitor Logs**: Watch `results/logs/` for progress
3. **Use Timeout**: Add `--timeout` for time limits
4. **GPU Not Required**: CPU is sufficient for this optimization

## Dataset Information

This project uses the [Mercari US Recommendation Dataset](https://huggingface.co/datasets/mercari-us/merrec) from Hugging Face.

**Dataset Statistics:**
- User browsing sessions with item views
- 6 feature categories: c0, c1, c2, brand, condition, size
- Sequence-based session data
- Rich item metadata

## Theory

### Problem Statement

Given user sessions with item sequences, learn which item attributes predict co-occurrence within sessions.

### Approach

1. **Pair Generation**: Create item pairs from sessions with sequence distance
2. **Target Score**: Decay function based on sequence distance
   - Score = decay_rate ^ sequence_distance
3. **Features**: Binary match indicators for each attribute
4. **Model**: Weighted sum + sigmoid normalization
5. **Optimization**: Minimize MSE on validation set

### Why This Works

Items viewed close together in a session are likely related. By learning which attributes match for these items, we discover what makes items similar in user's minds.

## Contributing

To extend this project:

1. Add new features in `data_loader.py`
2. Try different similarity functions in `optimizer.py`
3. Experiment with decay functions
4. Add new evaluation metrics

## License

This project is for educational and research purposes.

## Citation

If you use this code, please cite:

```
Mercari Item Similarity Optimization
https://github.com/yourusername/recommendation-ml
Dataset: mercari-us/merrec (Hugging Face)
```

## Support

For issues or questions:
1. Check this README
2. Review `config/config_example.yaml`
3. Check logs in `results/logs/`
4. Review example notebook

---

**Happy Optimizing! 🚀**



