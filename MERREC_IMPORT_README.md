# Mercari Dataset Import to MySQL/Cloud SQL

This guide shows you how to import data from the [Mercari US Recommendation Dataset](https://huggingface.co/datasets/mercari-us/merrec) into your MySQL or Cloud SQL database.

## 📊 Dataset Information

The Mercari dataset contains **25 columns**:

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | BIGINT | User identifier |
| `stime` | DATETIME | Session timestamp |
| `session_id` | VARCHAR | Session identifier |
| `sequence_id` | VARCHAR | Sequence identifier |
| `sequence_length` | INT | Length of sequence |
| `event_id` | VARCHAR | Event type (e.g., 'item_view') |
| `item_id` | BIGINT | Item identifier |
| `product_id` | VARCHAR | Product identifier |
| `name` | TEXT | Item name/title |
| `price` | DECIMAL | Item price |
| `c0_name` | VARCHAR | Category level 0 name |
| `c0_id` | INT | Category level 0 ID |
| `c1_name` | VARCHAR | Category level 1 name |
| `c1_id` | INT | Category level 1 ID |
| `c2_name` | VARCHAR | Category level 2 name |
| `c2_id` | INT | Category level 2 ID |
| `brand_name` | VARCHAR | Brand name |
| `brand_id` | INT | Brand ID |
| `item_condition_id` | INT | Condition ID |
| `item_condition_name` | VARCHAR | Condition name |
| `size_name` | VARCHAR | Size name |
| `size_id` | INT | Size ID |
| `color` | VARCHAR | Color |
| `shipper_id` | INT | Shipper ID |
| `shipper_name` | VARCHAR | Shipper name |

## 🚀 Quick Start

### 1. Setup Virtual Environment

```bash
cd /Users/yuseimoriwaki/src/curriculum_8_yusei_moriwaki

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install datasets huggingface_hub pandas pymysql python-dotenv cloud-sql-python-connector
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# For Local MySQL
DB_HOST=localhost
DB_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=mercari_db

# For Cloud SQL (add these)
CLOUD_SQL_INSTANCE=your-project:your-region:your-instance
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 3. Explore the Dataset

First, explore the dataset structure:

```bash
source venv/bin/activate
python explore_merrec.py
```

This will show you:
- All column names and types
- Sample data
- Null value counts

## 📥 Import Options

### Option A: Import to Local MySQL (Recommended for Testing)

**Prerequisites:**
- MySQL running locally (e.g., via Docker or installed)
- Database user with CREATE/INSERT permissions

**Run:**

```bash
source venv/bin/activate

# Import 1000 rows (default)
python import_merrec_local.py --verify

# Import 5000 rows
python import_merrec_local.py --limit 5000 --verify

# Import 10000 rows
python import_merrec_local.py --limit 10000
```

**Quick MySQL Setup with Docker:**

```bash
cd mysql
docker-compose up -d
```

Then update your `.env`:
```bash
DB_HOST=localhost
DB_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password  # from your docker-compose
MYSQL_DATABASE=mercari_db
```

### Option B: Import to Cloud SQL (Production)

**Prerequisites:**
- Google Cloud Project with Cloud SQL instance
- Cloud SQL Admin API enabled
- Proper authentication configured

**Run:**

```bash
source venv/bin/activate

# Import 1000 rows
python import_merrec_to_cloudsql.py --verify

# Import more rows
python import_merrec_to_cloudsql.py --limit 5000 --verify
```

**Authentication Options:**

1. **Application Default Credentials** (recommended):
   ```bash
   gcloud auth application-default login
   ```

2. **Service Account Key**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

## 📝 Script Details

### `explore_merrec.py`
- Explores dataset structure
- Shows sample data
- Displays column types and null counts

### `import_merrec_local.py`
- Imports to local MySQL
- Creates database if needed
- Handles all 25 columns
- Includes error handling and progress updates

### `import_merrec_to_cloudsql.py`
- Imports to Google Cloud SQL
- Uses Cloud SQL Python Connector
- Batch commits every 100 rows
- Includes verification option

## 🔍 Verify Import

Both scripts support the `--verify` flag to check the import:

```bash
python import_merrec_local.py --limit 1000 --verify
```

This will:
- Count total rows in the database
- Show sample of imported data
- Display column information

## 💾 Database Schema

The scripts create a table called `mercari_items` with:
- Auto-increment primary key (`id`)
- All 25 columns from the dataset
- Indexes on frequently queried columns:
  - `user_id`, `item_id`, `session_id`, `event_id`
  - `stime`, `c0_name`, `c1_name`, `brand_name`
- UTF-8 character set for international characters

## 📊 Query Examples

After importing, try these queries:

```sql
-- Count items by category
SELECT c0_name, COUNT(*) as count 
FROM mercari_items 
GROUP BY c0_name 
ORDER BY count DESC;

-- Average price by brand
SELECT brand_name, AVG(price) as avg_price, COUNT(*) as items
FROM mercari_items 
WHERE brand_name IS NOT NULL
GROUP BY brand_name 
ORDER BY items DESC 
LIMIT 20;

-- User activity
SELECT user_id, COUNT(*) as views, COUNT(DISTINCT item_id) as unique_items
FROM mercari_items 
GROUP BY user_id 
ORDER BY views DESC 
LIMIT 10;

-- Items viewed over time
SELECT DATE(stime) as date, COUNT(*) as views
FROM mercari_items 
GROUP BY DATE(stime) 
ORDER BY date;
```

## 🎯 Performance Tips

1. **Start Small**: Test with `--limit 1000` first
2. **Batch Size**: Scripts commit every 100 rows automatically
3. **Indexes**: Already created on common query columns
4. **Monitor**: Watch for errors in the output
5. **Cloud SQL**: For large imports, consider increasing instance size temporarily

## 🔧 Troubleshooting

### Connection Errors

**Local MySQL:**
```bash
# Check if MySQL is running
docker ps  # if using Docker
mysql -u root -p  # test connection
```

**Cloud SQL:**
```bash
# Test gcloud auth
gcloud auth list

# Check Cloud SQL instance
gcloud sql instances list

# Test connection
gcloud sql connect INSTANCE_NAME --user=root
```

### Import Errors

- Check `.env` file configuration
- Verify database permissions
- Check available disk space
- Review error messages in output

### Dependencies

If you get import errors:
```bash
source venv/bin/activate
pip install --upgrade datasets huggingface_hub pandas pymysql python-dotenv cloud-sql-python-connector
```

## 📚 Additional Resources

- [Mercari Dataset on Hugging Face](https://huggingface.co/datasets/mercari-us/merrec)
- [Cloud SQL Python Connector Docs](https://cloud.google.com/sql/docs/mysql/connect-connectors)
- [PyMySQL Documentation](https://pymysql.readthedocs.io/)

## ✅ Next Steps

After importing:
1. Run some exploratory queries
2. Create additional indexes if needed
3. Build recommendation algorithms
4. Analyze user behavior patterns
5. Create visualizations

Enjoy working with the Mercari dataset! 🎉

