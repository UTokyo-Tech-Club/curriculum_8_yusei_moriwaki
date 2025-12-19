# 🔍 Debugging Cloud SQL Connection Issues

## Error: `Access denied for user 'Yusei'@'cloudsqlproxy~...'`

This error indicates that the database username is incorrect. The username 'Yusei' appears to be your system username, not your database username.

## Quick Fix Steps

### 1. Check Your Environment Variables

Run the debug script to see what values are being used:

```bash
cd /Users/yuseimoriwaki/src/uttc-hackathon/curriculum_8_yusei_moriwaki/hackathon-backend
python debug_cloudsql_connection.py
```

### 2. Verify Your .env File

Make sure you have a `.env` file in the `hackathon-backend` directory with the correct values:

```bash
# Check if .env exists
ls -la .env

# If it doesn't exist, create it
cat > .env << EOF
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PWD=your_actual_password_here
MYSQL_DATABASE=hackathon
EOF
```

**Important**: 
- `MYSQL_USER` should be the database username (usually `root`), NOT your system username
- `MYSQL_PWD` should be the database password (e.g., `H4ck@thon_2025!` based on the docs)

### 3. Verify Cloud SQL Users

Check what users exist in your Cloud SQL instance:

```bash
gcloud sql users list --instance=uttc
```

You should see a user that matches your `MYSQL_USER` value. If not, you need to create it:

```bash
gcloud sql users create root \
  --instance=uttc \
  --password=your_password_here
```

### 4. Verify Cloud SQL Proxy is Running

The Cloud SQL Proxy must be running for local connections:

```bash
# Check if proxy is running
ps aux | grep cloud-sql-proxy

# If not running, start it:
# Replace with your actual instance connection name
./cloud-sql-proxy term8-yusei-moriwaki:us-central1:uttc
```

The proxy should be listening on `localhost:3306`.

### 5. Test Connection Manually

Test the connection directly with MySQL client:

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p hackathon
# Enter your password when prompted
```

If this works, the issue is with the application configuration. If it doesn't, the issue is with the proxy or credentials.

## Common Issues and Solutions

### Issue 1: Wrong Username

**Symptom**: Error shows your system username instead of database username

**Solution**: 
- Set `MYSQL_USER=root` (or your actual database username) in `.env`
- Make sure `.env` is in the `hackathon-backend` directory
- Restart your application

### Issue 2: Password Not Set

**Symptom**: `Access denied` even with correct username

**Solution**:
- Set `MYSQL_PWD=your_password` in `.env`
- Make sure there are no extra spaces or quotes
- Password should match the one in Cloud SQL

### Issue 3: Cloud SQL Proxy Not Running

**Symptom**: Connection timeout or "Can't connect to MySQL server"

**Solution**:
- Start the proxy: `./cloud-sql-proxy PROJECT_ID:REGION:INSTANCE_NAME`
- Verify it's listening: `lsof -i :3306`
- Make sure `MYSQL_HOST=localhost` in your `.env`

### Issue 4: User Doesn't Exist in Cloud SQL

**Symptom**: `Access denied` with correct credentials

**Solution**:
- List users: `gcloud sql users list --instance=uttc`
- Create user if missing: `gcloud sql users create USERNAME --instance=uttc --password=PASSWORD`
- Grant permissions if needed

## Debugging Checklist

- [ ] `.env` file exists in `hackathon-backend/` directory
- [ ] `MYSQL_USER` is set to database username (not system username)
- [ ] `MYSQL_PWD` is set to correct password
- [ ] `MYSQL_HOST` is set to `localhost` (for proxy) or Cloud SQL IP
- [ ] `MYSQL_DATABASE` is set to `hackathon`
- [ ] Cloud SQL Proxy is running and listening on port 3306
- [ ] User exists in Cloud SQL instance
- [ ] Password matches Cloud SQL user password
- [ ] Can connect manually with `mysql` command

## Running the Debug Script

The debug script will check all of these automatically:

```bash
python debug_cloudsql_connection.py
```

This will show you:
1. Current environment variable values
2. Whether Cloud SQL Proxy is running
3. Test the actual database connection
4. Provide specific error messages and solutions

## Still Having Issues?

1. Check the logs when running alembic:
   ```bash
   alembic upgrade head --verbose
   ```

2. Enable SQLAlchemy echo to see the exact connection string:
   - Temporarily set `echo=True` in `app/models/base.py` (line 47)

3. Verify your Cloud SQL instance is accessible:
   ```bash
   gcloud sql instances describe uttc
   ```

4. Check Cloud SQL Proxy logs for connection attempts

