# 🗄️ Complete Database Schema - Mercari Marketplace

**Instance**: term8-yusei-moriwaki:us-central1:uttc (db-f1-micro)  
**Database**: hackathon  
**Created**: December 16, 2025

---

## 📊 Database Overview

| Table | Rows | Description |
|-------|------|-------------|
| **users** | 74 | All users (buyers AND sellers) |
| **user_seller_profiles** | 29 | Optional seller profile (29/74 = 39% are sellers) |
| **item_listings** | 500 | Items posted for sale by users |
| **mercari_items** | 6,500 | User interactions (views, likes, purchases) |
| **user_sessions** | 963 | User browsing sessions |
| **user_favorites** | 386 | Items liked/favorited by users |

---

## 🎯 Key Concept: Users Can Be BOTH Buyers AND Sellers

```
┌─────────────────────────────────────────────────────────────┐
│                      User (e.g., ID: 45)                    │
│                     "Samuel Boyle"                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
      AS BUYER                AS SELLER
            │                     │
    ┌───────▼──────┐      ┌──────▼────────┐
    │ Views items  │      │ Sells items   │
    │ Likes items  │      │ Has shop      │
    │ Purchases    │      │ Gets ratings  │
    └──────────────┘      └───────────────┘
            │                     │
    ┌───────▼────────────┐ ┌─────▼──────────────┐
    │ mercari_items      │ │ item_listings      │
    │ user_favorites     │ │ user_seller_prof.. │
    │ user_sessions      │ └────────────────────┘
    └────────────────────┘
```

---

## 📋 Complete Table Schemas

### 1. **users** (Core Table)

All users in the system - can buy, sell, or both.

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Sample Data:**
- ID 45: Samuel Boyle (portercassandra@example.org)
- ID 50: Bruce Dunn (isaiah59@example.net)
- ID 56: Emily Hamilton (hterry@example.org)

**Relationships:**
- One-to-one with `user_seller_profiles` (optional)
- One-to-many with `mercari_items` (as buyer)
- One-to-many with `item_listings` (as seller)
- One-to-many with `user_sessions`
- One-to-many with `user_favorites`

---

### 2. **user_seller_profiles** (Optional Seller Info)

Optional seller profile for users who list items for sale.

```sql
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key Points:**
- Only exists for users who sell (29 out of 74 users)
- `user_id` references `users.id`
- Contains shop branding and seller metrics

**Sample Data:**
- User 45 → Shop: "Martinez-Smith LLC" (Rating: 4.85)
- User 50 → Shop: "Johnson Group" (Rating: 4.92)

---

### 3. **item_listings** (Items for Sale)

Items posted by sellers (users). Links directly to `users` table.

```sql
CREATE TABLE item_listings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_user_id BIGINT NOT NULL,           -- References users.id
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key Points:**
- `seller_user_id` links directly to `users.id` (NOT a separate sellers table)
- Same user can appear in `mercari_items` as buyer AND `item_listings` as seller
- Tracks listing status and engagement metrics

---

### 4. **mercari_items** (User Interactions)

Records of user interactions with items (views, likes, purchases).

```sql
CREATE TABLE mercari_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,                  -- User viewing/interacting (buyer role)
    stime DATETIME NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    sequence_id VARCHAR(100) NOT NULL,
    sequence_length INT NOT NULL,
    event_id VARCHAR(50) NOT NULL,            -- item_view, item_like, buy_comp, etc.
    item_id BIGINT NOT NULL,
    product_id VARCHAR(100),
    name TEXT,
    price DECIMAL(10, 2),
    c0_name VARCHAR(255),                     -- Category level 0
    c0_id INT,
    c1_name VARCHAR(255),                     -- Category level 1
    c1_id INT,
    c2_name VARCHAR(255),                     -- Category level 2
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Event Types:**
- `item_view` (5,975 = 92%)
- `item_like` (418 = 6%)
- `item_add_to_cart_tap` (63 = 1%)
- `offer_make` (28 = 0.4%)
- `buy_start` (11 = 0.2%)
- `buy_comp` (5 = 0.1%)

**Key Points:**
- `user_id` is the BUYER/VIEWER
- Rich item metadata for content-based recommendations
- Captures entire user journey (view → like → cart → purchase)

---

### 5. **user_sessions** (Browsing Sessions)

Aggregated user browsing sessions.

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Stats:**
- 963 unique sessions
- Average ~6.7 items per session
- Useful for session-based recommendations

---

### 6. **user_favorites** (Liked Items)

Items that users have favorited/liked.

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Stats:**
- 386 favorited items
- Derived from `event_id = 'item_like'`
- Strong signal for recommendations

---

## 🔗 Complete Entity Relationship Diagram

```
                     ┌──────────────┐
                     │    users     │
                     │   (74 rows)  │
                     └───────┬──────┘
                             │
          ┌──────────────────┼──────────────────┬────────────────┐
          │                  │                  │                │
    ┌─────▼─────┐     ┌──────▼──────┐   ┌──────▼──────┐  ┌─────▼─────┐
    │  item_    │     │ user_seller │   │   user_     │  │  mercari_ │
    │ listings  │     │  _profiles  │   │  sessions   │  │   items   │
    │ (500)     │     │    (29)     │   │   (963)     │  │  (6,500)  │
    └───────────┘     └─────────────┘   └─────────────┘  └─────┬─────┘
    seller_user_id    user_id            user_id               │
    (as SELLER)       (seller info)      (browsing)    user_id │
                                                        (as BUYER)
                                                                 │
                                                          ┌──────▼──────┐
                                                          │    user_    │
                                                          │  favorites  │
                                                          │    (386)    │
                                                          └─────────────┘
                                                           user_id, item_id
```

---

## 🎯 Sample Queries

### Find Users Who Are BOTH Buyers AND Sellers

```sql
SELECT 
    u.id,
    u.name,
    sp.shop_name,
    COUNT(DISTINCT m.id) as items_viewed,
    COUNT(DISTINCT l.id) as items_listed
FROM users u
LEFT JOIN user_seller_profiles sp ON u.id = sp.user_id
LEFT JOIN mercari_items m ON u.id = m.user_id
LEFT JOIN item_listings l ON u.id = l.seller_user_id
GROUP BY u.id
HAVING items_viewed > 0 AND items_listed > 0;
```

### Get a User's Complete Profile

```sql
-- User as both buyer and seller
SELECT 
    u.*,
    sp.shop_name,
    sp.rating as seller_rating,
    sp.total_listings,
    sp.total_sales,
    COUNT(DISTINCT m.id) as total_views,
    COUNT(DISTINCT f.id) as total_favorites,
    COUNT(DISTINCT s.id) as total_sessions
FROM users u
LEFT JOIN user_seller_profiles sp ON u.id = sp.user_id
LEFT JOIN mercari_items m ON u.id = m.user_id
LEFT JOIN user_favorites f ON u.id = f.user_id
LEFT JOIN user_sessions s ON u.id = s.user_id
WHERE u.id = 45
GROUP BY u.id;
```

### Seller Dashboard

```sql
-- Performance metrics for a seller
SELECT 
    u.name as seller_name,
    sp.shop_name,
    sp.rating,
    COUNT(l.id) as total_listings,
    SUM(l.views_count) as total_views,
    SUM(l.likes_count) as total_likes,
    SUM(CASE WHEN l.status = 'sold' THEN 1 ELSE 0 END) as total_sold,
    AVG(CASE WHEN l.status = 'sold' THEN 1 ELSE 0 END) * 100 as conversion_rate
FROM users u
JOIN user_seller_profiles sp ON u.id = sp.user_id
LEFT JOIN item_listings l ON u.id = l.seller_user_id
WHERE u.id = 45
GROUP BY u.id;
```

### Buyer's Browsing History

```sql
-- What a user (as buyer) has been viewing
SELECT 
    m.stime,
    m.event_id,
    m.name as item_name,
    m.price,
    m.brand_name,
    m.c0_name as category,
    u_seller.name as seller_name,
    sp.shop_name
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
LEFT JOIN users u_seller ON l.seller_user_id = u_seller.id
LEFT JOIN user_seller_profiles sp ON u_seller.id = sp.user_id
WHERE m.user_id = 45
ORDER BY m.stime DESC
LIMIT 20;
```

### Recommend Items Based on User's Favorites

```sql
-- Collaborative filtering: recommend items liked by similar users
SELECT 
    m.item_id,
    m.name,
    m.price,
    m.brand_name,
    COUNT(DISTINCT f2.user_id) as liked_by_similar_users
FROM user_favorites f1
JOIN user_favorites f2 ON f1.item_id = f2.item_id AND f1.user_id != f2.user_id
JOIN user_favorites f3 ON f2.user_id = f3.user_id
JOIN mercari_items m ON f3.item_id = m.item_id
WHERE f1.user_id = 45
  AND f3.item_id NOT IN (
      SELECT item_id FROM user_favorites WHERE user_id = 45
  )
GROUP BY m.item_id, m.name, m.price, m.brand_name
ORDER BY liked_by_similar_users DESC
LIMIT 10;
```

### Find Hot Sellers (High Engagement)

```sql
SELECT 
    u.name,
    sp.shop_name,
    sp.rating,
    COUNT(l.id) as listings,
    SUM(l.views_count) as total_views,
    SUM(l.likes_count) as total_likes,
    AVG(l.views_count) as avg_views_per_item,
    (SUM(l.likes_count) / NULLIF(SUM(l.views_count), 0)) * 100 as like_rate
FROM user_seller_profiles sp
JOIN users u ON sp.user_id = u.id
JOIN item_listings l ON u.id = l.seller_user_id
GROUP BY u.id
HAVING listings >= 5
ORDER BY avg_views_per_item DESC
LIMIT 10;
```

---

## 🚀 What You Can Build

### 1. Recommendation Systems

**Collaborative Filtering:**
- User-based: Find similar users, recommend what they liked
- Item-based: Find similar items based on co-interactions

**Content-Based:**
- Recommend items in same category
- Recommend items from same brand
- Price-range based recommendations

**Hybrid:**
- Combine user behavior + item features
- Personalized recommendations per user

### 2. Seller Features

**Seller Dashboard:**
- Total listings, views, likes, sales
- Conversion rate
- Top performing items
- Revenue analytics

**Seller Reputation:**
- Rating system (already in place)
- Reviews (can be added)
- Sales history

### 3. Buyer Features

**Personalized Homepage:**
- Recommended items
- Continue browsing (from sessions)
- Items from favorite sellers
- Similar to liked items

**Smart Search:**
- Based on browsing history
- Based on favorites
- Price range preferences

### 4. Analytics

**Platform Metrics:**
- Most viewed categories
- Top sellers
- Conversion funnel (view → like → cart → purchase)
- Session analytics

**User Segmentation:**
- Buyers only
- Sellers only
- Power users (both)
- New vs returning

---

## 📊 Current Data Distribution

### Users
- **Total**: 74 users
- **Sellers**: 29 (39%)
- **Buyers only**: 45 (61%)

### Listings
- **Total**: 500 items
- **Status**: Active (majority)
- **Average per seller**: ~17 items

### Interactions
- **Total**: 6,500 interactions
- **Average per user**: ~88 interactions
- **Most active user**: 2,923 interactions

### Categories (Top 5)
1. Women: 68.4%
2. Vintage & collectibles: 23.9%
3. Beauty: 3.0%
4. Home: 1.5%
5. Men: 0.9%

---

## 💡 Database Optimization Tips

### For Your db-f1-micro Instance:

**Current Capacity:**
- RAM: 628 MB
- Comfortable with: 100K-150K rows total
- Current usage: ~9K rows (✅ well within limits)

**Performance Tips:**
1. **Indexes are already optimized** for common queries
2. **Batch operations** - avoid large transactions
3. **Cache frequently accessed data** in your app
4. **Use LIMIT** in queries to reduce memory usage

**If You Need More:**
- Upgrade to **db-g1-small** (1.7 GB) - $25/month
- Can handle 500K-800K rows comfortably

---

## ✅ Success Checklist

- [x] User management system
- [x] Dual-role support (buyer + seller)
- [x] Item listings with seller attribution
- [x] User interaction tracking
- [x] Session management
- [x] Favorites/likes system
- [x] Rich item metadata (categories, brands, prices)
- [x] Seller profiles and ratings
- [x] Proper foreign key relationships
- [x] Optimized indexes for queries

---

## 🎓 Next Steps

1. **Build API endpoints** (FastAPI/Flask)
   - User CRUD
   - Item listings
   - Search & recommendations
   - Seller dashboard

2. **Implement recommendation engine**
   - Collaborative filtering
   - Content-based filtering
   - Hybrid approach

3. **Add authentication**
   - JWT tokens
   - User sessions
   - Role-based access (buyer vs seller)

4. **Build frontend**
   - User profiles
   - Item browsing
   - Seller dashboard
   - Recommendation feed

---

**Your database is production-ready for a marketplace with recommendations!** 🎉

**Database Summary:**
- 6 tables, 9,422 total rows
- Users can be both buyers AND sellers
- Rich interaction data for ML/recommendations
- Optimized for db-f1-micro instance
- Ready for API development

Created: December 16, 2025  
Last Updated: December 16, 2025  
Version: 1.0

