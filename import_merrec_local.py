import os
from datasets import load_dataset
import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Local MySQL connection parameters (for testing)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE", "mercari_db")

def get_local_connection():
    """Create a connection to local MySQL"""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"✓ Database '{DB_NAME}' ready")
    finally:
        conn.close()

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
    print("✓ Table 'mercari_items' created successfully")

def clean_value(value):
    """Clean and convert values for SQL insertion"""
    if pd.isna(value):
        return None
    if value == 'None':
        return None
    return value

def load_and_insert_data(limit=1000):
    """Load dataset from Hugging Face and insert into local MySQL"""
    
    print(f"Loading dataset from Hugging Face (limit: {limit} rows)...")
    dataset = load_dataset("mercari-us/merrec", split="train", streaming=True)
    
    print(f"Taking first {limit} rows...")
    data_iter = iter(dataset.take(limit))
    rows = list(data_iter)
    df = pd.DataFrame(rows)
    
    print(f"✓ Loaded {len(df)} rows with {len(df.columns)} columns")
    
    # Create database if needed
    create_database_if_not_exists()
    
    # Connect to MySQL
    print("\nConnecting to local MySQL...")
    conn = get_local_connection()
    
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
                        conn.commit()
                        
                except Exception as e:
                    error_count += 1
                    print(f"  Error inserting row {idx}: {e}")
                    continue
            
            conn.commit()
            
            print(f"\n{'='*80}")
            print(f"✓ Import Complete!")
            print(f"{'='*80}")
            print(f"Successfully inserted: {inserted_count} rows")
            print(f"Errors: {error_count} rows")
            
    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("\n✓ Connection closed")

def verify_import(limit=10):
    """Verify the imported data"""
    print("\n" + "="*80)
    print("VERIFYING IMPORT")
    print("="*80)
    
    conn = get_local_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM mercari_items")
            result = cursor.fetchone()
            print(f"\nTotal rows in database: {result['total']}")
            
            cursor.execute(f"SELECT * FROM mercari_items ORDER BY created_at DESC LIMIT {limit}")
            rows = cursor.fetchall()
            
            print(f"\nSample of last {limit} inserted rows:")
            print("-" * 80)
            for row in rows:
                name = row['name'][:50] if row['name'] else 'N/A'
                print(f"ID: {row['id']} | User: {row['user_id']} | Item: {name} | Price: ${row['price']}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Mercari dataset to local MySQL')
    parser.add_argument('--limit', type=int, default=1000, 
                        help='Number of rows to import (default: 1000)')
    parser.add_argument('--verify', action='store_true', 
                        help='Verify the import after completion')
    
    args = parser.parse_args()
    
    print("="*80)
    print("MERCARI DATASET IMPORT TO LOCAL MYSQL")
    print("="*80)
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"Limit: {args.limit} rows")
    print("="*80)
    
    load_and_insert_data(limit=args.limit)
    
    if args.verify:
        verify_import()
    
    print("\n✓ Done!")

