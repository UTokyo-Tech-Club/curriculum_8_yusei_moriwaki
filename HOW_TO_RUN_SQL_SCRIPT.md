# 📝 How to Run the Item Listings SQL Script in GCP Console

## 🎯 What This Does

The `complete_item_listings.sql` script will:
- ✅ Find all items not yet in `item_listings` (~4,774 items)
- ✅ Assign them to your 29 sellers (power-law distribution)
- ✅ Calculate views, likes, and status for each item
- ✅ Bulk insert all items in one transaction
- ✅ Update seller statistics
- ✅ Show you a complete summary

**Expected time**: 2-5 minutes

---

## 📋 Step-by-Step Instructions

### 1. **Open Google Cloud Console**

Go to: https://console.cloud.google.com/

### 2. **Navigate to Cloud SQL**

- Click the hamburger menu (☰) in top left
- Click **SQL** (under Databases section)
- Click on your instance: **uttc**

### 3. **Open Cloud Shell Editor** (Option A - Recommended)

1. Click the **three dots (⋮)** next to your instance name
2. Select **"Open Cloud Shell Editor"**
3. In the Cloud Shell that opens, create the SQL file:

```bash
# Create the SQL file
cat > complete_item_listings.sql << 'EOF'
[Paste the entire contents of complete_item_listings.sql here]
EOF

# Connect to your database
gcloud sql connect uttc --user=root --database=hackathon

# When prompted, enter your password: H4ck@thon_2025!

# Run the script
source complete_item_listings.sql;
```

### 4. **OR Use the Web Console** (Option B - Easier but may timeout)

1. Click your instance **uttc**
2. Click **"Databases"** tab in the left menu
3. Click on **hackathon** database
4. Click **"Open in Cloud Shell"** or **"Query"** button

**If using Query interface:**
- Copy the entire contents of `complete_item_listings.sql`
- Paste into the query editor
- Click **"Run"**

⚠️ **Note**: Large scripts may timeout in the web interface. Use Cloud Shell (Option A) for reliability.

---

## 🔍 What to Expect

### During Execution:

```
Query OK, 29 rows affected
Query OK, 4774 rows affected
Query OK, 4774 rows affected
...
```

### Final Output:

```
=== FINAL DATABASE SUMMARY ===
┌─────────────────────┬───────┐
│ metric              │ count │
├─────────────────────┼───────┤
│ Total Users         │    74 │
│ Users Who Sell      │    29 │
│ Total Item Listings │  5274 │  ← Should be ~5,274
│ Active Listings     │  5xxx │
│ Sold Items          │    xx │
└─────────────────────┴───────┘

=== TOP 10 SELLERS ===
[Shows top sellers with their listing counts]

✅ ITEM LISTINGS POPULATION COMPLETE!
Total listings: 5274 items
```

---

## ⚠️ Important Notes

### Before Running:

1. **Backup** (optional but recommended):
   ```sql
   CREATE TABLE item_listings_backup AS SELECT * FROM item_listings;
   ```

2. **Check current status**:
   ```sql
   SELECT COUNT(*) FROM item_listings;
   -- Should show ~500 rows
   ```

### If Something Goes Wrong:

**Script fails mid-way:**
- The script uses temporary tables, so partial data won't corrupt your database
- Just re-run the script - it will only add items not already in the table

**Timeout error:**
- Use Cloud Shell (Option A) instead of web console
- The script is optimized but db-f1-micro might be slow

**Lock/Deadlock error:**
- Wait 30 seconds and try again
- Make sure no other operations are running on the database

---

## 🔧 Alternative: Run in Smaller Batches

If the full script times out, run it in batches:

### Batch 1: Items 1-1500
```sql
INSERT INTO item_listings (seller_user_id, item_id, product_id, listed_at, status, views_count, likes_count)
SELECT 
    (SELECT user_id FROM user_seller_profiles ORDER BY RAND() LIMIT 1) as seller_user_id,
    m.item_id,
    m.product_id,
    MIN(m.stime) as listed_at,
    CASE WHEN MAX(CASE WHEN m.event_id IN ('buy_comp') THEN 1 ELSE 0 END) = 1 THEN 'sold' ELSE 'active' END,
    COUNT(*) as views_count,
    SUM(CASE WHEN m.event_id = 'item_like' THEN 1 ELSE 0 END) as likes_count
FROM mercari_items m
LEFT JOIN item_listings l ON m.item_id = l.item_id
WHERE l.item_id IS NULL
GROUP BY m.item_id, m.product_id
LIMIT 1500;
```

### Check progress:
```sql
SELECT COUNT(*) FROM item_listings;
```

### Repeat with increasing limits until all items are added.

---

## ✅ Verification After Completion

Run these queries to verify everything worked:

```sql
-- 1. Check total listings
SELECT COUNT(*) as total FROM item_listings;
-- Expected: ~5,274

-- 2. Check all items are assigned to sellers
SELECT COUNT(*) as unassigned FROM item_listings WHERE seller_user_id IS NULL;
-- Expected: 0

-- 3. Check seller distribution
SELECT 
    COUNT(DISTINCT seller_user_id) as sellers_with_items,
    AVG(listing_count) as avg_per_seller,
    MAX(listing_count) as max_per_seller
FROM (
    SELECT seller_user_id, COUNT(*) as listing_count
    FROM item_listings
    GROUP BY seller_user_id
) t;

-- 4. Verify seller stats are updated
SELECT 
    SUM(total_listings) as sum_listings,
    (SELECT COUNT(*) FROM item_listings) as actual_listings
FROM user_seller_profiles;
-- These should match!
```

---

## 🎉 Success Criteria

After running, you should have:
- ✅ **~5,274 items** in `item_listings`
- ✅ All items assigned to one of 29 sellers
- ✅ Seller statistics updated (`total_listings`, `total_sales`)
- ✅ Views, likes, and status calculated for each item
- ✅ Power-law distribution (some sellers have many items, most have fewer)

---

## 📞 Need Help?

If you encounter issues:

1. **Check Cloud SQL logs** in GCP Console
2. **Verify database connection**: `SHOW TABLES;`
3. **Check current state**: `SELECT COUNT(*) FROM item_listings;`
4. **Try smaller batches** if timeouts occur

---

**Ready to populate your database!** 🚀

Just copy `complete_item_listings.sql` and run it in GCP Cloud Console!

