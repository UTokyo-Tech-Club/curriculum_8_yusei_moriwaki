import os
from datasets import load_dataset
import pandas as pd
import pymysql
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Local MySQL connection parameters
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

def create_mercari_table_fast(cursor):
    """Create table WITHOUT indexes for faster bulk insert"""
    
    # Drop table if exists for clean import
    cursor.execute("DROP TABLE IF EXISTS mercari_items")
    
    create_table_sql = """
    CREATE TABLE mercari_items (
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    
    cursor.execute(create_table_sql)
    print("✓ Table created (indexes will be added after import)")

def add_indexes(cursor):
    """Add indexes AFTER bulk import for better performance"""
    print("\nAdding indexes (this improves query performance)...")
    
    indexes = [
        "CREATE INDEX idx_user_id ON mercari_items(user_id)",
        "CREATE INDEX idx_item_id ON mercari_items(item_id)",
        "CREATE INDEX idx_session_id ON mercari_items(session_id)",
        "CREATE INDEX idx_event_id ON mercari_items(event_id)",
        "CREATE INDEX idx_stime ON mercari_items(stime)",
        "CREATE INDEX idx_c0_name ON mercari_items(c0_name)",
        "CREATE INDEX idx_c1_name ON mercari_items(c1_name)",
        "CREATE INDEX idx_brand_name ON mercari_items(brand_name)"
    ]
    
    for idx_sql in indexes:
        cursor.execute(idx_sql)
    
    print("✓ All indexes created")

def clean_value(value):
    """Clean and convert values for SQL insertion"""
    if pd.isna(value):
        return None
    if value == 'None':
        return None
    return value

def load_and_insert_data_fast(limit=200000, batch_size=500):
    """FAST bulk import using batch inserts"""
    
    start_time = datetime.now()
    
    print(f"🚀 FAST IMPORT MODE")
    print(f"Loading dataset from Hugging Face (limit: {limit:,} rows)...")
    dataset = load_dataset("mercari-us/merrec", split="train", streaming=True)
    
    print(f"Streaming data in batches of {batch_size}...")
    
    # Create database if needed
    create_database_if_not_exists()
    
    # Connect to MySQL
    print("Connecting to MySQL...")
    conn = get_local_connection()
    
    # Optimize MySQL settings for bulk insert
    with conn.cursor() as cursor:
        cursor.execute("SET autocommit=0")
        cursor.execute("SET unique_checks=0")
        cursor.execute("SET foreign_key_checks=0")
        print("✓ MySQL optimized for bulk insert")
    
    try:
        with conn.cursor() as cursor:
            # Create table without indexes
            print("Creating table...")
            create_mercari_table_fast(cursor)
            
            # Prepare INSERT statement
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
            
            print(f"\n🔄 Importing {limit:,} rows in batches of {batch_size}...")
            
            batch = []
            inserted_count = 0
            error_count = 0
            
            # Stream and process in batches
            for row_dict in dataset.take(limit):
                try:
                    values = (
                        int(row_dict['user_id']),
                        row_dict['stime'],
                        str(row_dict['session_id']),
                        str(row_dict['sequence_id']),
                        int(row_dict['sequence_length']),
                        str(row_dict['event_id']),
                        int(row_dict['item_id']),
                        clean_value(row_dict['product_id']),
                        clean_value(row_dict['name']),
                        clean_value(row_dict['price']),
                        clean_value(row_dict['c0_name']),
                        int(row_dict['c0_id']) if pd.notna(row_dict['c0_id']) else None,
                        clean_value(row_dict['c1_name']),
                        int(row_dict['c1_id']) if pd.notna(row_dict['c1_id']) else None,
                        clean_value(row_dict['c2_name']),
                        int(row_dict['c2_id']) if pd.notna(row_dict['c2_id']) else None,
                        clean_value(row_dict['brand_name']),
                        int(row_dict['brand_id']) if pd.notna(row_dict['brand_id']) else None,
                        int(row_dict['item_condition_id']) if pd.notna(row_dict['item_condition_id']) else None,
                        clean_value(row_dict['item_condition_name']),
                        clean_value(row_dict['size_name']),
                        int(row_dict['size_id']) if pd.notna(row_dict['size_id']) else None,
                        clean_value(row_dict['color']),
                        int(row_dict['shipper_id']) if pd.notna(row_dict['shipper_id']) else None,
                        clean_value(row_dict['shipper_name'])
                    )
                    
                    batch.append(values)
                    
                    # Insert batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        cursor.executemany(insert_sql, batch)
                        conn.commit()
                        inserted_count += len(batch)
                        
                        # Progress update
                        elapsed = (datetime.now() - start_time).total_seconds()
                        rate = inserted_count / elapsed if elapsed > 0 else 0
                        percent = (inserted_count / limit) * 100
                        print(f"  ⚡ {inserted_count:,}/{limit:,} ({percent:.1f}%) - {rate:.0f} rows/sec - {elapsed:.0f}s elapsed")
                        
                        batch = []
                        
                except Exception as e:
                    error_count += 1
                    if error_count < 5:  # Only print first few errors
                        print(f"  ⚠️  Error: {e}")
                    continue
            
            # Insert remaining batch
            if batch:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                inserted_count += len(batch)
            
            # Add indexes after bulk insert
            add_indexes(cursor)
            
            conn.commit()
            
            # Re-enable checks
            cursor.execute("SET unique_checks=1")
            cursor.execute("SET foreign_key_checks=1")
            cursor.execute("SET autocommit=1")
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            print(f"\n{'='*80}")
            print(f"✅ FAST IMPORT COMPLETE!")
            print(f"{'='*80}")
            print(f"Successfully inserted: {inserted_count:,} rows")
            print(f"Errors: {error_count} rows")
            print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
            print(f"Average speed: {inserted_count/total_time:.0f} rows/second")
            print(f"{'='*80}")
            
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
            print(f"\n✓ Total rows in database: {result['total']:,}")
            
            # Quick stats
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT user_id) as users,
                    COUNT(DISTINCT item_id) as items,
                    AVG(price) as avg_price
                FROM mercari_items
            """)
            stats = cursor.fetchone()
            print(f"✓ Unique users: {stats['users']:,}")
            print(f"✓ Unique items: {stats['items']:,}")
            print(f"✓ Average price: ${stats['avg_price']:.2f}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='FAST Import Mercari dataset to local MySQL')
    parser.add_argument('--limit', type=int, default=200000, 
                        help='Number of rows to import (default: 200,000)')
    parser.add_argument('--batch-size', type=int, default=500,
                        help='Batch size for inserts (default: 500)')
    parser.add_argument('--verify', action='store_true', 
                        help='Verify the import after completion')
    
    args = parser.parse_args()
    
    print("="*80)
    print("⚡ MERCARI DATASET FAST IMPORT TO LOCAL MYSQL")
    print("="*80)
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"Import size: {args.limit:,} rows")
    print(f"Batch size: {args.batch_size}")
    print("="*80)
    
    load_and_insert_data_fast(limit=args.limit, batch_size=args.batch_size)
    
    if args.verify:
        verify_import()
    
    print("\n✅ Done!")

