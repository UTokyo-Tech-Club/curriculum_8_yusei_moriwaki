import os
from datasets import load_dataset
import pandas as pd
from google.cloud.sql.connector import Connector
import pymysql
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Cloud SQL connection parameters
INSTANCE_CONNECTION_NAME = os.getenv("CLOUD_SQL_INSTANCE")  # e.g., "project:region:instance"
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE")

def get_cloud_sql_connection():
    """Create a connection to Cloud SQL using the Cloud SQL Python Connector"""
    connector = Connector()
    
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME
    )
    return conn

def create_mercari_table(cursor):
    """Create table for Mercari recommendation data with ALL 25 columns"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS mercari_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id BIGINT NOT NULL,
        stime DATETIME NOT NULL,
        session_id VARCHAR(255) NOT NULL,
        sequence_id VARCHAR(100) NOT NULL,
        sequence_length INT NOT NULL,
        event_id VARCHAR(50) NOT NULL,
        item_id BIGINT NOT NULL,
        product_id VARCHAR(100),
        name TEXT,
        price DECIMAL(10, 2),
        c0_name VARCHAR(255),
        c0_id INT,
        c1_name VARCHAR(255),
        c1_id INT,
        c2_name VARCHAR(255),
        c2_id INT,
        brand_name VARCHAR(255),
        brand_id INT,
        item_condition_id INT,
        item_condition_name VARCHAR(100),
        size_name VARCHAR(255),
        size_id INT,
        color VARCHAR(255),
        shipper_id INT,
        shipper_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id),
        INDEX idx_item_id (item_id),
        INDEX idx_session_id (session_id),
        INDEX idx_event_id (event_id),
        INDEX idx_stime (stime),
        INDEX idx_c0_name (c0_name),
        INDEX idx_c1_name (c1_name),
        INDEX idx_brand_name (brand_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    cursor.execute(create_table_sql)
    print("✓ Table created successfully")

def clean_value(value):
    """Clean and convert values for SQL insertion"""
    if pd.isna(value):
        return None
    if value == 'None':
        return None
    return value

def load_and_insert_data(limit=1000):
    """Load dataset from Hugging Face and insert into Cloud SQL"""
    
    print(f"Loading dataset from Hugging Face (limit: {limit} rows)...")
    # Load the dataset
    dataset = load_dataset("mercari-us/merrec", split="train", streaming=True)
    
    # Convert to pandas DataFrame (taking only first 'limit' rows)
    print(f"Taking first {limit} rows...")
    data_iter = iter(dataset.take(limit))
    rows = list(data_iter)
    df = pd.DataFrame(rows)
    
    print(f"✓ Loaded {len(df)} rows with {len(df.columns)} columns")
    print(f"Columns: {df.columns.tolist()}")
    
    # Connect to Cloud SQL
    print("\nConnecting to Cloud SQL...")
    conn = get_cloud_sql_connection()
    
    try:
        with conn.cursor() as cursor:
            # Create table
            print("Creating table (if not exists)...")
            create_mercari_table(cursor)
            
            # Insert data
            print(f"\nInserting {len(df)} rows...")
            
            insert_sql = """
            INSERT INTO mercari_items 
            (user_id, stime, session_id, sequence_id, sequence_length, event_id, 
             item_id, product_id, name, price, 
             c0_name, c0_id, c1_name, c1_id, c2_name, c2_id,
             brand_name, brand_id, item_condition_id, item_condition_name,
             size_name, size_id, color, shipper_id, shipper_name)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
             %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s)
            """
            
            inserted_count = 0
            error_count = 0
            
            for idx, row in df.iterrows():
                try:
                    cursor.execute(insert_sql, (
                        int(row['user_id']),
                        row['stime'],
                        str(row['session_id']),
                        str(row['sequence_id']),
                        int(row['sequence_length']),
                        str(row['event_id']),
                        int(row['item_id']),
                        clean_value(row['product_id']),
                        clean_value(row['name']),
                        clean_value(row['price']),
                        clean_value(row['c0_name']),
                        int(row['c0_id']) if pd.notna(row['c0_id']) else None,
                        clean_value(row['c1_name']),
                        int(row['c1_id']) if pd.notna(row['c1_id']) else None,
                        clean_value(row['c2_name']),
                        int(row['c2_id']) if pd.notna(row['c2_id']) else None,
                        clean_value(row['brand_name']),
                        int(row['brand_id']) if pd.notna(row['brand_id']) else None,
                        int(row['item_condition_id']) if pd.notna(row['item_condition_id']) else None,
                        clean_value(row['item_condition_name']),
                        clean_value(row['size_name']),
                        int(row['size_id']) if pd.notna(row['size_id']) else None,
                        clean_value(row['color']),
                        int(row['shipper_id']) if pd.notna(row['shipper_id']) else None,
                        clean_value(row['shipper_name'])
                    ))
                    inserted_count += 1
                    
                    if inserted_count % 100 == 0:
                        print(f"  Inserted {inserted_count} rows...")
                        conn.commit()  # Commit every 100 rows
                        
                except Exception as e:
                    error_count += 1
                    print(f"  Error inserting row {idx}: {e}")
                    continue
            
            # Final commit
            conn.commit()
            
            print(f"\n{'='*80}")
            print(f"✓ Import Complete!")
            print(f"{'='*80}")
            print(f"Successfully inserted: {inserted_count} rows")
            print(f"Errors: {error_count} rows")
            print(f"Total processed: {len(df)} rows")
            
    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("\n✓ Connection closed")

def verify_import(limit=10):
    """Verify the imported data by querying the database"""
    print("\n" + "="*80)
    print("VERIFYING IMPORT")
    print("="*80)
    
    conn = get_cloud_sql_connection()
    try:
        with conn.cursor() as cursor:
            # Count total rows
            cursor.execute("SELECT COUNT(*) as total FROM mercari_items")
            result = cursor.fetchone()
            print(f"\nTotal rows in database: {result['total']}")
            
            # Show sample rows
            cursor.execute(f"SELECT * FROM mercari_items ORDER BY created_at DESC LIMIT {limit}")
            rows = cursor.fetchall()
            
            print(f"\nSample of last {limit} inserted rows:")
            print("-" * 80)
            for row in rows:
                print(f"ID: {row['id']} | User: {row['user_id']} | Item: {row['name'][:50]} | Price: ${row['price']}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Mercari dataset to Cloud SQL')
    parser.add_argument('--limit', type=int, default=1000, 
                        help='Number of rows to import (default: 1000)')
    parser.add_argument('--verify', action='store_true', 
                        help='Verify the import after completion')
    
    args = parser.parse_args()
    
    print("="*80)
    print("MERCARI DATASET IMPORT TO CLOUD SQL")
    print("="*80)
    print(f"Limit: {args.limit} rows")
    print(f"Instance: {INSTANCE_CONNECTION_NAME}")
    print(f"Database: {DB_NAME}")
    print("="*80)
    
    # Load and insert data
    load_and_insert_data(limit=args.limit)
    
    # Verify if requested
    if args.verify:
        verify_import()
    
    print("\n✓ Done!")

