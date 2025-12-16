import os
from google.cloud.sql.connector import Connector
import pymysql
from dotenv import load_dotenv
import random

load_dotenv()

def get_connection():
    connector = Connector()
    return connector.connect(
        os.getenv('CLOUD_SQL_INSTANCE'),
        'pymysql',
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        db=os.getenv('MYSQL_DATABASE'),
        cursorclass=pymysql.cursors.DictCursor
    )

print('='*80)
print('ASSIGNING ITEMS TO SELLERS')
print('='*80)

conn = get_connection()

try:
    with conn.cursor() as cursor:
        # Get unique items (simplified - just item_id)
        print('\n1. Getting unique items...')
        cursor.execute('SELECT DISTINCT item_id FROM mercari_items ORDER BY item_id')
        item_ids = [row['item_id'] for row in cursor.fetchall()]
        print(f'   ✓ Found {len(item_ids)} unique items')
        
        # Get sellers
        print('\n2. Getting sellers...')
        cursor.execute('SELECT user_id FROM user_seller_profiles')
        seller_ids = [row['user_id'] for row in cursor.fetchall()]
        print(f'   ✓ Found {len(seller_ids)} sellers')
        
        # Assign items in batches
        print(f'\n3. Assigning items (batches of 100)...')
        seller_weights = [1/(i+1) for i in range(len(seller_ids))]
        
        batch_size = 100
        total = len(item_ids)
        
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_items = item_ids[batch_start:batch_end]
            
            # Build batch insert
            values = []
            for item_id in batch_items:
                seller_id = random.choices(seller_ids, weights=seller_weights, k=1)[0]
                values.append(f"({seller_id}, {item_id}, 'active')")
            
            # Execute batch (IGNORE duplicates)
            sql = f'''
                INSERT IGNORE INTO item_listings (seller_user_id, item_id, status)
                VALUES {','.join(values)}
            '''
            cursor.execute(sql)
            conn.commit()
            
            print(f'   Assigned {batch_end}/{total} items ({batch_end/total*100:.1f}%)')
        
        print(f'\n✓ All {total} items assigned!')
        
        # Update statistics
        print('\n4. Updating seller statistics...')
        cursor.execute('''
            UPDATE user_seller_profiles sp
            SET total_listings = (
                SELECT COUNT(*) 
                FROM item_listings 
                WHERE seller_user_id = sp.user_id
            )
        ''')
        conn.commit()
        print('   ✓ Statistics updated')
        
        # Show summary
        print('\n' + '='*80)
        print('SUMMARY')
        print('='*80)
        cursor.execute('SELECT COUNT(*) as c FROM item_listings')
        total_listings = cursor.fetchone()['c']
        
        cursor.execute('''
            SELECT u.name, sp.shop_name, sp.total_listings
            FROM user_seller_profiles sp
            JOIN users u ON sp.user_id = u.id
            ORDER BY sp.total_listings DESC
            LIMIT 5
        ''')
        
        print(f'\nTotal listings: {total_listings:,}')
        print('\nTop 5 Sellers:')
        for seller in cursor.fetchall():
            print(f'  {seller["name"]:20s} ({seller["shop_name"]:25s}) - {seller["total_listings"]} items')
        
        print('\n' + '='*80)
        print('✅ COMPLETE!')
        print('='*80)
        
finally:
    conn.close()

