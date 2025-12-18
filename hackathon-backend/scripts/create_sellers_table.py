import os
from google.cloud.sql.connector import Connector
import pymysql
from dotenv import load_dotenv
from faker import Faker
import random

load_dotenv()

fake = Faker()

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

def create_sellers_and_listings():
    """Create user seller profiles and item_listings (users can be both buyers AND sellers)"""
    
    print("="*80)
    print("CREATING USER SELLER PROFILES & ITEM LISTINGS")
    print("="*80)
    print("Note: Users can be BOTH buyers and sellers!")
    
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            # 1. Drop existing tables if they exist
            print("\n1. Dropping existing tables (if any)...")
            cursor.execute("DROP TABLE IF EXISTS item_listings")
            cursor.execute("DROP TABLE IF EXISTS user_seller_profiles")
            print("   ✓ Dropped existing tables")
            
            # 2. Create user_seller_profiles table (optional profile for users who sell)
            print("\n2. Creating user_seller_profiles table...")
            cursor.execute("""
                CREATE TABLE user_seller_profiles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    shop_name VARCHAR(255) NOT NULL,
                    shop_description TEXT,
                    rating DECIMAL(3,2) DEFAULT 5.00,
                    total_sales INT DEFAULT 0,
                    total_listings INT DEFAULT 0,
                    joined_as_seller_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_shop_name (shop_name),
                    INDEX idx_rating (rating)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✓ User seller profiles table created")
            
            # 3. Create item_listings table (links items to users as sellers)
            print("\n3. Creating item_listings table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS item_listings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    seller_user_id BIGINT NOT NULL,
                    item_id BIGINT NOT NULL,
                    product_id VARCHAR(100),
                    listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('active', 'sold', 'removed') DEFAULT 'active',
                    views_count INT DEFAULT 0,
                    likes_count INT DEFAULT 0,
                    FOREIGN KEY (seller_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_item (item_id),
                    INDEX idx_seller_items (seller_user_id),
                    INDEX idx_item_id (item_id),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✓ Item listings table created (seller_user_id references users)")
            
            # 4. Get unique items
            print("\n4. Analyzing unique items...")
            cursor.execute("""
                SELECT DISTINCT item_id, product_id, MIN(stime) as first_seen
                FROM mercari_items
                GROUP BY item_id, product_id
                ORDER BY item_id
            """)
            
            items = cursor.fetchall()
            print(f"   ✓ Found {len(items)} unique items")
            
            # 5. Get existing users and make some of them sellers
            cursor.execute("SELECT id FROM users")
            all_users = [row['id'] for row in cursor.fetchall()]
            
            # In real marketplaces, ~30-50% of users are also sellers
            seller_ratio = 0.4
            num_sellers = int(len(all_users) * seller_ratio)
            
            print(f"\n5. Creating seller profiles for {num_sellers}/{len(all_users)} users...")
            
            # Randomly select users to be sellers
            seller_user_ids = random.sample(all_users, min(num_sellers, len(all_users)))
            
            for user_id in seller_user_ids:
                shop_name = fake.company()
                shop_desc = f"Welcome to {shop_name}! Quality items at great prices."
                rating = round(random.uniform(3.5, 5.0), 2)
                
                cursor.execute("""
                    INSERT INTO user_seller_profiles (user_id, shop_name, shop_description, rating)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE user_id = user_id
                """, (user_id, shop_name, shop_desc, rating))
                
                if len(seller_user_ids) % 10 == 0 and seller_user_ids.index(user_id) % 10 == 0:
                    print(f"   Created {seller_user_ids.index(user_id) + 1}/{len(seller_user_ids)} seller profiles...")
            
            conn.commit()
            print(f"   ✓ Created {len(seller_user_ids)} seller profiles")
            
            # 6. Assign items to sellers (users who sell)
            print(f"\n6. Assigning {len(items)} items to seller users...")
            
            # Use power law distribution: some sellers have many items, most have few
            seller_weights = [1/(i+1) for i in range(len(seller_user_ids))]
            
            assigned = 0
            for item in items:
                # Pick a seller user (weighted random - popular sellers have more items)
                seller_user_id = random.choices(seller_user_ids, weights=seller_weights, k=1)[0]
                
                # Get view and like counts for this item
                cursor.execute("""
                    SELECT 
                        COUNT(*) as views,
                        SUM(CASE WHEN event_id = 'item_like' THEN 1 ELSE 0 END) as likes
                    FROM mercari_items
                    WHERE item_id = %s
                """, (item['item_id'],))
                
                stats = cursor.fetchone()
                
                # Determine status based on events
                cursor.execute("""
                    SELECT event_id FROM mercari_items 
                    WHERE item_id = %s AND event_id IN ('buy_comp', 'buy_start')
                    LIMIT 1
                """, (item['item_id'],))
                
                has_purchase = cursor.fetchone()
                status = 'sold' if has_purchase else 'active'
                
                # Insert listing
                cursor.execute("""
                    INSERT INTO item_listings 
                    (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    seller_user_id,
                    item['item_id'],
                    item['product_id'],
                    item['first_seen'],
                    status,
                    stats['views'] or 0,
                    stats['likes'] or 0
                ))
                
                assigned += 1
                if assigned % 500 == 0:
                    conn.commit()
                    print(f"   Assigned {assigned}/{len(items)} items...")
            
            conn.commit()
            print(f"   ✓ Assigned all {assigned} items to sellers")
            
            # 7. Update seller statistics
            print("\n7. Calculating seller statistics...")
            cursor.execute("""
                UPDATE user_seller_profiles sp
                SET 
                    total_listings = (
                        SELECT COUNT(*) 
                        FROM item_listings 
                        WHERE seller_user_id = sp.user_id
                    ),
                    total_sales = (
                        SELECT COUNT(*) 
                        FROM item_listings 
                        WHERE seller_user_id = sp.user_id AND status = 'sold'
                    )
            """)
            conn.commit()
            print("   ✓ Updated seller statistics")
            
            print(f"\n{'='*80}")
            print("✅ SELLER PROFILES & LISTINGS CREATED!")
            print("   Users can now be BOTH buyers AND sellers!")
            print(f"{'='*80}")
            
    finally:
        conn.close()

def show_seller_summary():
    """Show summary of sellers and their listings"""
    
    print("\n" + "="*80)
    print("SELLERS & LISTINGS SUMMARY")
    print("="*80)
    
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            # Count
            cursor.execute("SELECT COUNT(*) as count FROM users")
            total_users = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM user_seller_profiles")
            sellers_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM item_listings")
            listings_count = cursor.fetchone()['count']
            
            print(f"\n📊 Overview:")
            print(f"   Total users: {total_users:,}")
            print(f"   Users who sell: {sellers_count:,} ({sellers_count/total_users*100:.1f}%)")
            print(f"   Total listings: {listings_count:,}")
            
            # Top sellers by listings
            print(f"\n🏪 Top Sellers (Users with Most Listings):")
            cursor.execute("""
                SELECT 
                    u.name as user_name,
                    sp.shop_name,
                    sp.rating,
                    sp.total_listings,
                    SUM(l.views_count) as total_views,
                    SUM(l.likes_count) as total_likes,
                    sp.total_sales
                FROM user_seller_profiles sp
                JOIN users u ON sp.user_id = u.id
                LEFT JOIN item_listings l ON sp.user_id = l.seller_user_id
                GROUP BY sp.id
                ORDER BY sp.total_listings DESC
                LIMIT 5
            """)
            
            for seller in cursor.fetchall():
                print(f"   {seller['user_name']:20s} ({seller['shop_name']:25s}) | {seller['total_listings']:3d} items | ⭐ {seller['rating']}")
            
            # Listing status
            print(f"\n📦 Listing Status:")
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM item_listings
                GROUP BY status
            """)
            
            for row in cursor.fetchall():
                print(f"   {row['status']:10s}: {row['count']:,} items")
            
            # Sample: User who both buys and sells
            print(f"\n👤 Sample: User Who is BOTH Buyer & Seller:")
            cursor.execute("""
                SELECT 
                    u.name as user_name,
                    u.email,
                    sp.shop_name,
                    sp.total_listings,
                    sp.total_sales,
                    COUNT(DISTINCT m.id) as items_viewed_as_buyer
                FROM users u
                JOIN user_seller_profiles sp ON u.id = sp.user_id
                LEFT JOIN mercari_items m ON u.id = m.user_id
                GROUP BY u.id
                HAVING items_viewed_as_buyer > 0
                LIMIT 1
            """)
            
            dual_role = cursor.fetchone()
            if dual_role:
                print(f"   User: {dual_role['user_name']} ({dual_role['email']})")
                print(f"   As BUYER: Viewed {dual_role['items_viewed_as_buyer']} items")
                print(f"   As SELLER: Shop '{dual_role['shop_name']}' with {dual_role['total_listings']} listings, {dual_role['total_sales']} sales")
            
            # Sample listing with full details
            print(f"\n📝 Sample Listing:")
            cursor.execute("""
                SELECT 
                    u.name as seller_name,
                    sp.shop_name,
                    m.name as item_name,
                    m.price,
                    l.views_count,
                    l.likes_count,
                    l.status
                FROM item_listings l
                JOIN users u ON l.seller_user_id = u.id
                JOIN user_seller_profiles sp ON u.id = sp.user_id
                JOIN mercari_items m ON l.item_id = m.item_id
                LIMIT 1
            """)
            
            sample = cursor.fetchone()
            if sample:
                print(f"   Seller: {sample['seller_name']} (Shop: {sample['shop_name']})")
                print(f"   Item: {sample['item_name']}")
                print(f"   Price: ${sample['price']}")
                print(f"   Views: {sample['views_count']}, Likes: {sample['likes_count']}")
                print(f"   Status: {sample['status']}")
            
            print("\n" + "="*80)
            print("✅ Complete marketplace structure ready!")
            print("="*80)
            
    finally:
        conn.close()

if __name__ == "__main__":
    create_sellers_and_listings()
    show_seller_summary()

