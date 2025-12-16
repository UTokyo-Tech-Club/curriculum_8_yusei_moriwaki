from datasets import load_dataset
import pandas as pd

def explore_dataset():
    """Explore the structure of the Mercari dataset"""
    print("Loading dataset from Hugging Face...")
    dataset = load_dataset("mercari-us/merrec", split="train", streaming=True)
    
    # Take first 10 rows to examine structure
    print("Taking first 10 rows...")
    data_iter = iter(dataset.take(10))
    rows = list(data_iter)
    df = pd.DataFrame(rows)
    
    print("\n" + "="*80)
    print("DATASET INFORMATION")
    print("="*80)
    print(f"\nNumber of columns: {len(df.columns)}")
    print(f"\nColumn names: {df.columns.tolist()}")
    
    print("\n" + "="*80)
    print("DATA TYPES")
    print("="*80)
    print(df.dtypes)
    
    print("\n" + "="*80)
    print("SAMPLE DATA (First Row)")
    print("="*80)
    for col in df.columns:
        value = df[col].iloc[0]
        # Truncate long text for display
        if isinstance(value, str) and len(value) > 100:
            value = value[:100] + "..."
        print(f"{col}: {value}")
    
    print("\n" + "="*80)
    print("NULL VALUE COUNTS")
    print("="*80)
    print(df.isnull().sum())
    
    print("\n" + "="*80)
    print("FIRST 3 ROWS")
    print("="*80)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    print(df.head(3))
    
    return df

if __name__ == "__main__":
    df = explore_dataset()
    print("\n✓ Exploration complete!")

