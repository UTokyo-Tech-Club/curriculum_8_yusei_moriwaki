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

def create_users_table():
    """Create users table and populate with realistic fake data"""
    
    print("="*80)
    print("CREATING USERS TABLE")
    print("="*80)
    
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            print("\n1. Creating users table...")
            
            # Drop table if exists to ensure clean schema
            cursor.execute("DROP TABLE IF EXISTS user_favorites")
            cursor.execute("DROP TABLE IF EXISTS user_sessions")
            cursor.execute("DROP TABLE IF EXISTS users")
            print("   ✓ Dropped existing tables (if any)")
            
            # Create table
            cursor.execute("""
                CREATE TABLE users (
                    id BIGINT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    avatar VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("   ✓ Users table created")
            
            # Get unique user_ids from mercari_items
            print("\n2. Fetching unique users from mercari_items...")
            cursor.execute("""
                SELECT DISTINCT user_id, MIN(stime) as first_activity
                FROM mercari_items
                GROUP BY user_id
                ORDER BY user_id
            """)
            
            user_data = cursor.fetchall()
            print(f"   ✓ Found {len(user_data)} unique users")
            
            # Generate and insert realistic user data
            print("\n3. Generating fake user profiles...")
            
            inserted = 0
            for user in user_data:
                user_id = user['user_id']
                first_activity = user['first_activity']
                
                # Generate fake data
                name = fake.name()
                email = fake.email()
                
                # Avatar from DiceBear API (free avatar generator)
                avatar_styles = ['avataaars', 'bottts', 'personas', 'lorelei', 'micah']
                style = random.choice(avatar_styles)
                avatar = f'https://api.dicebear.com/7.x/{style}/svg?seed={user_id}'
                
                # Insert user
                cursor.execute("""
                    INSERT INTO users (id, email, name, avatar, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        email = VALUES(email),
                        name = VALUES(name),
                        avatar = VALUES(avatar)
                """, (user_id, email, name, avatar, first_activity))
                inserted += 1
                
                if inserted % 10 == 0:
                    print(f"   Generated {inserted}/{len(user_data)} users...")
            
            conn.commit()
            print(f"   ✓ Inserted {inserted} users")
            
            # Show sample
            print("\n4. Sample users:")
            cursor.execute("SELECT id, name, email, avatar FROM users ORDER BY id LIMIT 5")
            for user in cursor.fetchall():
                print(f"   ID {user['id']}: {user['name']} ({user['email']})")
            
            # Stats
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()['total']
            
            print(f"\n{'='*80}")
            print(f"✅ SUCCESS! Created {total} users in the database")
            print(f"{'='*80}")
            
    finally:
        conn.close()

def create_relationship_tables():
    """Create user_sessions and user_favorites tables"""
    
    print("\n" + "="*80)
    print("CREATING RELATIONSHIP TABLES")
    print("="*80)
    
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            # Create user_sessions table
            print("\n1. Creating user_sessions table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    item_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_session (session_id),
                    INDEX idx_user_sessions (user_id, start_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✓ user_sessions table created")
            
            # Populate sessions
            print("\n2. Populating user sessions...")
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_id, start_time, item_count)
                SELECT 
                    user_id,
                    session_id,
                    MIN(stime) as start_time,
                    COUNT(*) as item_count
                FROM mercari_items
                GROUP BY user_id, session_id
                ON DUPLICATE KEY UPDATE item_count = VALUES(item_count)
            """)
            sessions_count = cursor.rowcount
            conn.commit()
            print(f"   ✓ Inserted {sessions_count} sessions")
            
            # Create user_favorites table
            print("\n3. Creating user_favorites table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_favorites (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    item_id BIGINT NOT NULL,
                    favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_favorite (user_id, item_id),
                    INDEX idx_user_favorites (user_id),
                    INDEX idx_item_favorites (item_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✓ user_favorites table created")
            
            # Populate favorites from 'item_like' events
            print("\n4. Populating user favorites from 'item_like' events...")
            cursor.execute("""
                INSERT INTO user_favorites (user_id, item_id, favorited_at)
                SELECT user_id, item_id, stime
                FROM mercari_items
                WHERE event_id = 'item_like'
                ON DUPLICATE KEY UPDATE favorited_at = VALUES(favorited_at)
            """)
            favorites_count = cursor.rowcount
            conn.commit()
            print(f"   ✓ Inserted {favorites_count} favorites")
            
            print(f"\n{'='*80}")
            print(f"✅ Relationship tables created!")
            print(f"   - {sessions_count} user sessions")
            print(f"   - {favorites_count} user favorites")
            print(f"{'='*80}")
            
    finally:
        conn.close()

def show_summary():
    """Show summary of all tables"""
    
    print("\n" + "="*80)
    print("DATABASE SUMMARY")
    print("="*80)
    
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            # Count tables
            tables = ['users', 'mercari_items', 'user_sessions', 'user_favorites']
            
            print("\n📊 Table Counts:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"   {table:20s}: {count:,} rows")
            
            # Show user with most activity
            print("\n👤 Most Active Users:")
            cursor.execute("""
                SELECT 
                    u.id,
                    u.name,
                    u.email,
                    COUNT(m.id) as total_interactions
                FROM users u
                JOIN mercari_items m ON u.id = m.user_id
                GROUP BY u.id, u.name, u.email
                ORDER BY total_interactions DESC
                LIMIT 5
            """)
            for user in cursor.fetchall():
                print(f"   {user['name']:25s} - {user['total_interactions']} interactions")
            
            # Event type distribution
            print("\n📈 Event Distribution:")
            cursor.execute("""
                SELECT event_id, COUNT(*) as count
                FROM mercari_items
                GROUP BY event_id
                ORDER BY count DESC
            """)
            for event in cursor.fetchall():
                print(f"   {event['event_id']:20s}: {event['count']:,}")
            
            print("\n" + "="*80)
            print("✅ ALL DONE! Your database is ready for recommendations!")
            print("="*80)
            
    finally:
        conn.close()

if __name__ == "__main__":
    create_users_table()
    create_relationship_tables()
    show_summary()

