-- ==============================================================================
-- Simple Batch Item Listings Population (db-f1-micro optimized)
-- ==============================================================================
-- Run this script in smaller steps to avoid deadlocks on small instances
-- Copy and paste EACH SECTION separately, waiting between sections
-- ==============================================================================

-- ==============================================================================
-- SECTION 1: Insert items in small batch (500 items)
-- Copy and run this section first
-- ==============================================================================

INSERT IGNORE INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE 
        WHEN MAX(CASE WHEN m.event_id = 'buy_comp' THEN 1 ELSE 0 END) = 1 THEN 'sold' 
        ELSE 'active' 
    END as status,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id
LIMIT 500;

-- Check progress
SELECT 'Batch 1 Complete' as status, COUNT(*) as total_listings FROM item_listings;

-- ==============================================================================
-- SECTION 2: Insert next batch (500 more items)
-- Wait 10 seconds, then run this
-- ==============================================================================

INSERT IGNORE INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE 
        WHEN MAX(CASE WHEN m.event_id = 'buy_comp' THEN 1 ELSE 0 END) = 1 THEN 'sold' 
        ELSE 'active' 
    END as status,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id
LIMIT 500;

SELECT 'Batch 2 Complete' as status, COUNT(*) as total_listings FROM item_listings;

-- ==============================================================================
-- SECTION 3: Insert next batch (500 more items)
-- Wait 10 seconds, then run this
-- ==============================================================================

INSERT IGNORE INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE 
        WHEN MAX(CASE WHEN m.event_id = 'buy_comp' THEN 1 ELSE 0 END) = 1 THEN 'sold' 
        ELSE 'active' 
    END as status,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id
LIMIT 500;

SELECT 'Batch 3 Complete' as status, COUNT(*) as total_listings FROM item_listings;

-- ==============================================================================
-- SECTION 4: Insert next batch (500 more items)
-- Wait 10 seconds, then run this
-- ==============================================================================

INSERT IGNORE INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE 
        WHEN MAX(CASE WHEN m.event_id = 'buy_comp' THEN 1 ELSE 0 END) = 1 THEN 'sold' 
        ELSE 'active' 
    END as status,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id
LIMIT 500;

SELECT 'Batch 4 Complete' as status, COUNT(*) as total_listings FROM item_listings;

-- ==============================================================================
-- SECTION 5: Insert next batch (500 more items)
-- Wait 10 seconds, then run this
-- ==============================================================================

INSERT IGNORE INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE 
        WHEN MAX(CASE WHEN m.event_id = 'buy_comp' THEN 1 ELSE 0 END) = 1 THEN 'sold' 
        ELSE 'active' 
    END as status,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id
LIMIT 500;

SELECT 'Batch 5 Complete' as status, COUNT(*) as total_listings FROM item_listings;

-- ==============================================================================
-- SECTION 6: Insert remaining items (all that's left)
-- Wait 10 seconds, then run this
-- ==============================================================================

INSERT IGNORE INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE 
        WHEN MAX(CASE WHEN m.event_id = 'buy_comp' THEN 1 ELSE 0 END) = 1 THEN 'sold' 
        ELSE 'active' 
    END as status,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id;

SELECT 'All Batches Complete!' as status, COUNT(*) as total_listings FROM item_listings;

-- ==============================================================================
-- SECTION 7: Update seller statistics
-- Run this after all items are inserted
-- ==============================================================================

UPDATE user_seller_profiles sp
SET total_listings = (
    SELECT COUNT(*) FROM item_listings WHERE seller_user_id = sp.user_id
)
WHERE sp.user_id IN (SELECT DISTINCT seller_user_id FROM item_listings);

UPDATE user_seller_profiles sp
SET total_sales = (
    SELECT COUNT(*) FROM item_listings WHERE seller_user_id = sp.user_id AND status = 'sold'
)
WHERE sp.user_id IN (SELECT DISTINCT seller_user_id FROM item_listings);

SELECT 'Statistics Updated!' as status;

-- ==============================================================================
-- SECTION 8: Final verification
-- ==============================================================================

SELECT '=== FINAL SUMMARY ===' as '';

SELECT 
    'Total Users' as metric,
    COUNT(*) as value
FROM users
UNION ALL
SELECT 'Users Who Sell', COUNT(*) FROM user_seller_profiles
UNION ALL
SELECT 'Item Listings', COUNT(*) FROM item_listings
UNION ALL
SELECT 'Active Listings', COUNT(*) FROM item_listings WHERE status = 'active'
UNION ALL
SELECT 'Sold Items', COUNT(*) FROM item_listings WHERE status = 'sold';

SELECT '=== TOP 5 SELLERS ===' as '';

SELECT 
    u.name,
    sp.shop_name,
    sp.total_listings,
    sp.total_sales
FROM user_seller_profiles sp
JOIN users u ON sp.user_id = u.id
ORDER BY sp.total_listings DESC
LIMIT 5;

SELECT '✅ COMPLETE! All items populated!' as final_status;

