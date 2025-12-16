# 📦 Mercari Dataset Import - Setup Complete!

I've created a complete solution to import the [Mercari US Recommendation Dataset](https://huggingface.co/datasets/mercari-us/merrec) into your Cloud SQL or local MySQL database.

## 📁 Files Created

### Core Scripts

1. **`explore_merrec.py`** ✅
   - Explores the dataset structure
   - Shows all 25 columns with data types
   - Displays sample data and null counts
   - **Run first to understand the data!**

2. **`import_merrec_local.py`** ✅
   - Imports to **local MySQL** database
   - Perfect for testing and development
   - Creates database if it doesn't exist
   - Handles all 25 columns automatically
   - Progress updates every 100 rows

3. **`import_merrec_to_cloudsql.py`** ✅
   - Imports to **Google Cloud SQL**
   - Uses Cloud SQL Python Connector
   - Production-ready with error handling
   - Batch commits for efficiency

4. **`quick_start.py`** ✅
   - Interactive setup helper
   - Checks prerequisites
   - Guides you through configuration
   - **Run this if you're not sure where to start!**

### Documentation

5. **`MERREC_IMPORT_README.md`** ✅
   - Comprehensive guide
   - Dataset schema documentation
   - Setup instructions for both local and Cloud SQL
   - Example SQL queries
   - Troubleshooting tips

6. **`requirements_merrec.txt`** ✅
   - All Python dependencies
   - Easy installation: `pip install -r requirements_merrec.txt`

## 🎯 What the Scripts Do

### Dataset Coverage: ALL 25 Columns! ✅

The scripts handle **every single column** from the Mercari dataset:

```
✓ user_id              - User identifier
✓ stime                - Timestamp
✓ session_id           - Session ID
✓ sequence_id          - Sequence ID  
✓ sequence_length      - Sequence length
✓ event_id             - Event type
✓ item_id              - Item ID
✓ product_id           - Product ID
✓ name                 - Item name
✓ price                - Price
✓ c0_name, c0_id       - Category level 0
✓ c1_name, c1_id       - Category level 1  
✓ c2_name, c2_id       - Category level 2
✓ brand_name, brand_id - Brand info
✓ item_condition_id    - Condition ID
✓ item_condition_name  - Condition name
✓ size_name, size_id   - Size info
✓ color                - Color
✓ shipper_id           - Shipper ID
✓ shipper_name         - Shipper name
```

### Database Features

- ✅ **Auto-creates table** with proper schema
- ✅ **Indexes** on frequently queried columns (user_id, item_id, category, brand, etc.)
- ✅ **UTF-8 support** for international characters
- ✅ **NULL handling** for missing data
- ✅ **Error recovery** - continues on individual row errors
- ✅ **Progress tracking** - updates every 100 rows
- ✅ **Verification** - built-in data verification option

## 🚀 Quick Start (3 Steps!)

### Step 1: Setup Environment

```bash
cd /Users/yuseimoriwaki/src/curriculum_8_yusei_moriwaki

# Activate virtual environment (already created!)
source venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements_merrec.txt
```

### Step 2: Configure Database

Create a `.env` file:

```bash
# For local MySQL testing
DB_HOST=localhost
DB_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=mercari_db

# For Cloud SQL (add this line)
CLOUD_SQL_INSTANCE=your-project:your-region:your-instance
```

### Step 3: Run Import!

```bash
# Option A: Explore first (recommended!)
python explore_merrec.py

# Option B: Import to local MySQL
python import_merrec_local.py --limit 1000 --verify

# Option C: Import to Cloud SQL  
python import_merrec_to_cloudsql.py --limit 1000 --verify
```

## 💡 Usage Examples

### Explore Dataset Structure
```bash
source venv/bin/activate
python explore_merrec.py
```

Output:
- Number of columns (25)
- Column names and types
- Sample data from first rows
- NULL value counts

### Import Small Test Set
```bash
# Import 1000 rows to test
python import_merrec_local.py --limit 1000 --verify
```

### Import Larger Dataset
```bash
# Import 10,000 rows
python import_merrec_local.py --limit 10000 --verify

# Import 50,000 rows
python import_merrec_to_cloudsql.py --limit 50000
```

### Verify Existing Import
```bash
python import_merrec_local.py --limit 0 --verify
```

## 📊 What You Can Do After Import

Once data is imported, try these SQL queries:

### 1. Top Categories
```sql
SELECT c0_name, COUNT(*) as count 
FROM mercari_items 
GROUP BY c0_name 
ORDER BY count DESC;
```

### 2. Average Price by Brand
```sql
SELECT brand_name, AVG(price) as avg_price, COUNT(*) as items
FROM mercari_items 
WHERE brand_name IS NOT NULL
GROUP BY brand_name 
ORDER BY items DESC 
LIMIT 20;
```

### 3. User Activity Analysis
```sql
SELECT user_id, 
       COUNT(*) as total_views,
       COUNT(DISTINCT item_id) as unique_items,
       AVG(price) as avg_price_viewed
FROM mercari_items 
GROUP BY user_id 
ORDER BY total_views DESC 
LIMIT 20;
```

### 4. Price Distribution
```sql
SELECT 
    CASE 
        WHEN price < 10 THEN 'Under $10'
        WHEN price < 50 THEN '$10-$50'
        WHEN price < 100 THEN '$50-$100'
        WHEN price < 200 THEN '$100-$200'
        ELSE 'Over $200'
    END as price_range,
    COUNT(*) as count
FROM mercari_items 
GROUP BY price_range
ORDER BY MIN(price);
```

## 🔧 Features & Benefits

| Feature | Local Script | Cloud SQL Script |
|---------|-------------|------------------|
| All 25 columns | ✅ | ✅ |
| Auto-create database | ✅ | ❌ (manual) |
| Progress tracking | ✅ | ✅ |
| Error handling | ✅ | ✅ |
| Batch commits | ✅ (every 100) | ✅ (every 100) |
| Verification | ✅ | ✅ |
| Indexes | ✅ | ✅ |
| UTF-8 support | ✅ | ✅ |

## 📝 Important Notes

1. **Start Small**: Always test with `--limit 1000` first
2. **Check Connection**: Verify database credentials in `.env`
3. **Monitor Progress**: Watch the console output for errors
4. **Cloud SQL Auth**: Make sure `gcloud auth` is configured
5. **Disk Space**: Ensure adequate space for your import size

## 🎓 Learning Opportunities

This setup teaches you:
- ✅ Working with Hugging Face datasets
- ✅ Database schema design
- ✅ ETL (Extract, Transform, Load) processes
- ✅ Cloud SQL connections
- ✅ Data validation and verification
- ✅ Production-ready error handling

## 🆘 Need Help?

1. **Run the quick start helper:**
   ```bash
   python quick_start.py
   ```

2. **Read the full documentation:**
   - `MERREC_IMPORT_README.md`

3. **Check prerequisites:**
   - Python 3.8+ ✅
   - Virtual environment ✅  
   - Dependencies installed ✅
   - `.env` configured ❓
   - Database accessible ❓

## ✅ Checklist

Before running imports:

- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Dependencies installed (`pip install -r requirements_merrec.txt`)
- [ ] `.env` file created with database credentials
- [ ] Database is accessible (test with mysql or gcloud)
- [ ] Explored dataset structure (`python explore_merrec.py`)
- [ ] Tested with small limit first (`--limit 1000`)

## 🎉 You're All Set!

Everything is ready to import the Mercari dataset. The scripts handle:
- ✅ All 25 columns
- ✅ Proper data types
- ✅ NULL values
- ✅ Error handling
- ✅ Progress tracking
- ✅ Verification

**Next step**: Configure your `.env` file and start importing!

```bash
# Quick command to get started
source venv/bin/activate
python explore_merrec.py
```

Happy data importing! 🚀

