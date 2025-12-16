# 🗄️ Database Schema - Mercari Recommendation System

## ✅ Successfully Created!

All tables have been created and populated in your Cloud SQL database.

---

## 📊 Database Overview

| Table | Rows | Description |
|-------|------|-------------|
| **users** | 74 | User profiles with email, name, avatar |
| **mercari_items** | 6,500 | User interactions with items |
| **user_sessions** | 963 | User browsing sessions |
| **user_favorites** | 386 | Items liked by users |

---

## 📋 Table Schemas

### 1. **users** 
Primary user information table

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
)
```

**Sample Data:**
- ID 45: Samuel Boyle (portercassandra@example.org)
- ID 50: Bruce Dunn (isaiah59@example.net)
- ID 56: Emily Hamilton (hterry@example.org)

**Features:**
- ✅ Realistic fake names generated with Faker
- ✅ Valid email addresses
- ✅ Avatar URLs from DiceBear API
- ✅ Created_at from first activity timestamp

---

### 2. **mercari_items**
User interactions with items (existing table)

**Columns:** 25 columns including:
- `id` - Auto-increment primary key
- `user_id` - References users(id)
- `item_id` - Item identifier
- `name` - Item name
- `price` - Item price
- `event_id` - Event type (item_view, item_like, etc.)
- ... and 19 more columns

**Key Indexes:**
- `idx_user_id` - Fast user lookup
- `idx_item_id` - Fast item lookup
- `idx_session_id` - Session tracking
- `idx_event_id` - Event filtering

---

### 3. **user_sessions**
User browsing sessions

```sql
CREATE TABLE user_sessions (
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
)
```

**Stats:**
- 963 unique sessions
- Average ~6.7 items per session
- Tracks user browsing patterns

---

### 4. **user_favorites**
Items favorited/liked by users

```sql
CREATE TABLE user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id BIGINT NOT NULL,
    favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, item_id),
    INDEX idx_user_favorites (user_id),
    INDEX idx_item_favorites (item_id)
)
```

**Stats:**
- 386 favorited items
- Derived from `event_id = 'item_like'`
- Average ~5.2 likes per active user

---

## 🔗 Relationships

```
users (74)
  ├─► mercari_items (6,500)
  │   └─ Foreign Key: user_id
  │
  ├─► user_sessions (963)
  │   └─ Foreign Key: user_id
  │
  └─► user_favorites (386)
      └─ Foreign Key: user_id
```

---

## 📈 Event Distribution

| Event Type | Count | Percentage |
|-----------|-------|------------|
| `item_view` | 5,975 | 91.9% |
| `item_like` | 418 | 6.4% |
| `item_add_to_cart_tap` | 63 | 1.0% |
| `offer_make` | 28 | 0.4% |
| `buy_start` | 11 | 0.2% |
| `buy_comp` | 5 | 0.1% |

---

## 👥 Top Active Users

1. **Christopher Greene** - 2,923 interactions (45%)
2. **Michael Curry** - 503 interactions (7.7%)
3. **William Conway** - 377 interactions (5.8%)
4. **Ethan Hall** - 372 interactions (5.7%)
5. **Krystal Green** - 288 interactions (4.4%)

---

## 🔍 Useful Queries

### Get user profile with activity
```sql
SELECT 
    u.*,
    COUNT(m.id) as total_interactions,
    COUNT(DISTINCT m.session_id) as sessions,
    COUNT(f.id) as favorites
FROM users u
LEFT JOIN mercari_items m ON u.id = m.user_id
LEFT JOIN user_favorites f ON u.id = f.user_id
WHERE u.id = 45
GROUP BY u.id;
```

### Get user's favorite items
```sql
SELECT 
    u.name as user_name,
    m.name as item_name,
    m.price,
    m.brand_name,
    f.favorited_at
FROM user_favorites f
JOIN users u ON f.user_id = u.id
JOIN mercari_items m ON f.item_id = m.item_id
WHERE u.id = 45
ORDER BY f.favorited_at DESC;
```

### Get user session history
```sql
SELECT 
    s.session_id,
    s.start_time,
    s.item_count,
    GROUP_CONCAT(DISTINCT m.c0_name) as categories_viewed
FROM user_sessions s
JOIN mercari_items m ON s.session_id = m.session_id
WHERE s.user_id = 45
GROUP BY s.id
ORDER BY s.start_time DESC;
```

### Collaborative filtering - similar users
```sql
-- Users who liked similar items
SELECT 
    u2.id,
    u2.name,
    COUNT(DISTINCT f2.item_id) as common_favorites
FROM user_favorites f1
JOIN user_favorites f2 ON f1.item_id = f2.item_id AND f1.user_id != f2.user_id
JOIN users u2 ON f2.user_id = u2.id
WHERE f1.user_id = 45
GROUP BY u2.id, u2.name
ORDER BY common_favorites DESC
LIMIT 10;
```

---

## 🎯 Ready for Recommendation System!

Your database now has:
- ✅ User profiles with realistic data
- ✅ Item interaction history
- ✅ Session tracking
- ✅ Favorite/like data
- ✅ Proper relationships and indexes

### Next Steps for Building Recommendations:

1. **Collaborative Filtering**
   - Use user_favorites to find similar users
   - Recommend items liked by similar users

2. **Content-Based Filtering**
   - Use mercari_items categories and brands
   - Recommend similar items based on features

3. **Session-Based**
   - Use user_sessions to predict next item
   - Sequence models (RNN/Transformer)

4. **Hybrid Approach**
   - Combine multiple signals
   - Weight by engagement (views, likes, purchases)

---

## 🔧 Maintenance

### Update user profile
```sql
UPDATE users 
SET name = 'New Name', email = 'newemail@example.com'
WHERE id = 45;
```

### Add new user
```sql
INSERT INTO users (id, email, name, avatar)
VALUES (999, 'newuser@example.com', 'New User', 'https://api.dicebear.com/7.x/avataaars/svg?seed=999');
```

### Get database size
```sql
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'hackathon'
ORDER BY (data_length + index_length) DESC;
```

---

**Database Instance:** term8-yusei-moriwaki:us-central1:uttc  
**Database Name:** hackathon  
**Created:** December 16, 2025  

✅ **All systems ready for recommendation engine development!**

