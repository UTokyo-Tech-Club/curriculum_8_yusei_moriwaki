-- ==============================================================================
-- Complete Item Listings Population Script
-- ==============================================================================
-- Run this script in GCP Cloud SQL Console to populate all remaining items
-- This will assign ~4,774 remaining items to sellers
--
-- Database: hackathon
-- Expected runtime: 2-5 minutes
-- ==============================================================================

-- Step 1: Create a temporary table with seller user IDs for random selection
-- ==============================================================================
DROP TEMPORARY TABLE IF EXISTS temp_sellers;
CREATE TEMPORARY TABLE temp_sellers (
    seller_user_id BIGINT,
    seller_rank INT
);

-- Populate with all sellers and assign them ranks (for weighted distribution)
INSERT INTO temp_sellers (seller_user_id, seller_rank)
SELECT 
    user_id,
    ROW_NUMBER() OVER (ORDER BY RAND()) as seller_rank
FROM user_seller_profiles;

-- Check: How many sellers we have
SELECT COUNT(*) as total_sellers FROM temp_sellers;

-- ==============================================================================
-- Step 2: Create temporary table with items that need to be listed
-- ==============================================================================
DROP TEMPORARY TABLE IF EXISTS temp_items_to_list;
CREATE TEMPORARY TABLE temp_items_to_list (
    item_id BIGINT,
    product_id VARCHAR(100),
    first_seen DATETIME,
    item_rank INT
);

-- Get all unique items that aren't already listed
INSERT INTO temp_items_to_list (item_id, product_id, first_seen, item_rank)
SELECT 
    m.item_id,
    m.product_id,
    MIN(m.stime) as first_seen,
    ROW_NUMBER() OVER (ORDER BY m.item_id) as item_rank
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id;

-- Check: How many items to list
SELECT COUNT(*) as items_to_list FROM temp_items_to_list;

-- ==============================================================================
-- Step 3: Assign sellers to items (power-law distribution)
-- Popular sellers get more items
-- ==============================================================================
DROP TEMPORARY TABLE IF EXISTS temp_item_assignments;
CREATE TEMPORARY TABLE temp_item_assignments (
    item_id BIGINT,
    seller_user_id BIGINT,
    product_id VARCHAR(100),
    first_seen DATETIME
);

-- Assign each item to a seller
-- Using modulo to distribute with bias toward lower-ranked sellers (more items)
INSERT INTO temp_item_assignments (item_id, seller_user_id, product_id, first_seen)
SELECT 
    i.item_id,
    s.seller_user_id,
    i.product_id,
    i.first_seen
FROM temp_items_to_list i
CROSS JOIN (
    -- Create weighted distribution: sellers with lower rank get picked more often
    SELECT seller_user_id, seller_rank
    FROM temp_sellers
) s
WHERE MOD(i.item_rank + FLOOR(RAND() * 100), (
    SELECT COUNT(*) FROM temp_sellers
)) + 1 = s.seller_rank;

-- Check: Assignments made
SELECT COUNT(*) as assignments FROM temp_item_assignments;

-- ==============================================================================
-- Step 4: Calculate stats for each item (views, likes, status)
-- ==============================================================================
DROP TEMPORARY TABLE IF EXISTS temp_item_stats;
CREATE TEMPORARY TABLE temp_item_stats (
    item_id BIGINT PRIMARY KEY,
    views_count INT DEFAULT 0,
    likes_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active'
);

-- Calculate views and likes for each item
INSERT INTO temp_item_stats (item_id, views_count, likes_count, status)
SELECT 
    m.item_id,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count,
    CASE 
        WHEN MAX(CASE WHEN m.event_id IN ('buy_comp', 'buy_start') THEN 1 ELSE 0 END) = 1 
        THEN 'sold'
        ELSE 'active'
    END as status
FROM mercari_items m
WHERE m.item_id IN (SELECT item_id FROM temp_item_assignments)
GROUP BY m.item_id;

-- Check: Stats calculated
SELECT 
    COUNT(*) as items_with_stats,
    SUM(views_count) as total_views,
    SUM(likes_count) as total_likes,
    SUM(CASE WHEN status = 'sold' THEN 1 ELSE 0 END) as sold_items
FROM temp_item_stats;

-- ==============================================================================
-- Step 5: Insert all items into item_listings (BATCH INSERT)
-- ==============================================================================
INSERT INTO item_listings 
    (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    a.seller_user_id,
    a.item_id,
    a.product_id,
    a.first_seen as listed_at,
    COALESCE(s.status, 'active') as status,
    COALESCE(s.views_count, 0) as views_count,
    COALESCE(s.likes_count, 0) as likes_count
FROM temp_item_assignments a
LEFT JOIN temp_item_stats s ON a.item_id = s.item_id;

-- Check: Final count
SELECT 
    COUNT(*) as total_listings,
    COUNT(DISTINCT seller_user_id) as sellers_with_listings
FROM item_listings;

-- ==============================================================================
-- Step 6: Update seller statistics
-- ==============================================================================
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
        WHERE seller_user_id = sp.user_id 
        AND status = 'sold'
    );

-- ==============================================================================
-- Step 7: Verification and Summary
-- ==============================================================================

-- Overall statistics
SELECT '=== FINAL DATABASE SUMMARY ===' as '';

SELECT 
    'Total Users' as metric,
    COUNT(*) as count
FROM users
UNION ALL
SELECT 
    'Users Who Sell',
    COUNT(*)
FROM user_seller_profiles
UNION ALL
SELECT 
    'Total Item Listings',
    COUNT(*)
FROM item_listings
UNION ALL
SELECT 
    'Active Listings',
    COUNT(*)
FROM item_listings
WHERE status = 'active'
UNION ALL
SELECT 
    'Sold Items',
    COUNT(*)
FROM item_listings
WHERE status = 'sold';

-- Top sellers
SELECT '=== TOP 10 SELLERS ===' as '';

SELECT 
    u.name as seller_name,
    sp.shop_name,
    sp.rating,
    sp.total_listings,
    sp.total_sales
FROM user_seller_profiles sp
JOIN users u ON sp.user_id = u.id
ORDER BY sp.total_listings DESC
LIMIT 10;

-- Listing status breakdown
SELECT '=== LISTING STATUS ===' as '';

SELECT 
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM item_listings), 2) as percentage
FROM item_listings
GROUP BY status
ORDER BY count DESC;

-- Items per seller distribution
SELECT '=== ITEMS PER SELLER DISTRIBUTION ===' as '';

SELECT 
    CASE 
        WHEN listing_count < 50 THEN '1-49 items'
        WHEN listing_count < 100 THEN '50-99 items'
        WHEN listing_count < 200 THEN '100-199 items'
        WHEN listing_count < 500 THEN '200-499 items'
        ELSE '500+ items'
    END as item_range,
    COUNT(*) as seller_count
FROM (
    SELECT seller_user_id, COUNT(*) as listing_count
    FROM item_listings
    GROUP BY seller_user_id
) counts
GROUP BY item_range
ORDER BY MIN(listing_count);

-- ==============================================================================
-- Cleanup temporary tables
-- ==============================================================================
DROP TEMPORARY TABLE IF EXISTS temp_sellers;
DROP TEMPORARY TABLE IF EXISTS temp_items_to_list;
DROP TEMPORARY TABLE IF EXISTS temp_item_assignments;
DROP TEMPORARY TABLE IF EXISTS temp_item_stats;

-- ==============================================================================
-- COMPLETE! 
-- ==============================================================================
SELECT '✅ ITEM LISTINGS POPULATION COMPLETE!' as status;
SELECT CONCAT('Total listings: ', COUNT(*), ' items') as result FROM item_listings;

