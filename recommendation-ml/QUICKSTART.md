# Quick Start Guide

Get up and running with Mercari Item Similarity Optimization in 5 minutes!

## 1. Setup (2 minutes)

```bash
cd recommendation-ml

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Quick Test Run (3-5 minutes)

```bash
# Run a quick test with small dataset
python train.py --trials 20 --sample-limit 10000
```

This will:
- Load 10,000 records from Hugging Face
- Generate training pairs
- Run 20 optimization trials
- Save results to `results/models/`
- Save logs to `results/logs/`

## 3. View Results

```bash
# Check the log
ls -lt results/logs/

# Check the results
ls -lt results/models/
```

Or open the Jupyter notebook:

```bash
jupyter notebook notebooks/analysis.ipynb
```

## 4. Full Training Run (30-60 minutes)

```bash
# Run with default config (better results)
python train.py

# Or customize
python train.py --trials 200 --sample-limit 100000
```

## Common Commands

```bash
# Use custom config
python train.py --config my_config.yaml

# Override specific parameters
python train.py --trials 50 --sample-limit 20000 --seed 123

# Set logging level
python train.py --log-level DEBUG

# Set timeout (in seconds)
python train.py --timeout 3600  # 1 hour
```

## Understanding Output

After training completes, you'll see:

```
TRAINING COMPLETE!
Experiment ID: 20250116_143022
Best validation MSE: 0.023456
Best validation R²: 0.876543

Top 3 most important features:
  1. c1: 0.3542
  2. brand: 0.2817
  3. c2: 0.1893
```

## Configuration Tips

Edit `config/config.yaml` to change:

- **sample_limit**: 10000 (quick) → 100000 (production)
- **n_trials**: 20 (quick) → 200 (thorough)
- **decay_rate**: 0.7-0.9 (how similarity decays with distance)
- **max_sequence_distance**: 5-15 (how far to look in sessions)

## Troubleshooting

**Out of memory?**
```bash
python train.py --sample-limit 20000 --max-distance 5
```

**Too slow?**
```bash
python train.py --trials 30 --timeout 1800
```

**Config error?**
```bash
# Copy example config
cp config/config_example.yaml config/config.yaml
```

## Next Steps

1. Review README.md for detailed documentation
2. Experiment with different configurations
3. Analyze results in Jupyter notebook
4. Use optimized parameters in your recommendation system

Happy optimizing! 🚀



