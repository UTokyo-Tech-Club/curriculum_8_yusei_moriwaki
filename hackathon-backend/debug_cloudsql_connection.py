#!/usr/bin/env python3
"""
Debug script to diagnose Cloud SQL connection issues from local machine.
This script will help identify configuration problems.
"""
import os
import sys

# Try to load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, that's okay - we'll use system env vars
    pass

print("=" * 80)
print("Cloud SQL Connection Debugger")
print("=" * 80)
print()

# Check environment variables
print("1. Environment Variables:")
print("-" * 80)
env_vars = {
    "MYSQL_HOST": os.getenv("MYSQL_HOST"),
    "MYSQL_USER": os.getenv("MYSQL_USER"),
    "MYSQL_PWD": os.getenv("MYSQL_PWD"),
    "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),  # Alternative name
    "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
    "CLOUD_SQL_UNIX_SOCKET": os.getenv("CLOUD_SQL_UNIX_SOCKET"),
}

for key, value in env_vars.items():
    if key in ["MYSQL_PWD", "MYSQL_PASSWORD"]:
        if value:
            print(f"  {key}: {'*' * len(value)} (length: {len(value)})")
        else:
            print(f"  {key}: <NOT SET>")
    else:
        print(f"  {key}: {value if value else '<NOT SET>'}")

print()
print("2. System Username (for comparison):")
print("-" * 80)
print(f"  System user: {os.getenv('USER') or os.getenv('USERNAME')}")
print()

# Check if Cloud SQL Proxy is running
print("3. Cloud SQL Proxy Status:")
print("-" * 80)
import subprocess
try:
    result = subprocess.run(
        ["ps", "aux"], 
        capture_output=True, 
        text=True, 
        timeout=5
    )
    if "cloud-sql-proxy" in result.stdout or "cloud_sql_proxy" in result.stdout:
        print("  ✓ Cloud SQL Proxy appears to be running")
        # Try to extract the connection string
        for line in result.stdout.split('\n'):
            if "cloud-sql-proxy" in line or "cloud_sql_proxy" in line:
                print(f"  Process: {line.strip()[:100]}")
    else:
        print("  ✗ Cloud SQL Proxy does not appear to be running")
        print("  → You need to start it with:")
        print("    ./cloud-sql-proxy PROJECT_ID:REGION:INSTANCE_NAME")
except Exception as e:
    print(f"  ⚠ Could not check proxy status: {e}")

print()

# Test database connection
print("4. Testing Database Connection:")
print("-" * 80)

try:
    import pymysql
    
    # Get connection parameters
    host = env_vars["MYSQL_HOST"] or "localhost"
    user = env_vars["MYSQL_USER"] or env_vars.get("MYSQL_PASSWORD") or "root"
    password = env_vars["MYSQL_PWD"] or env_vars["MYSQL_PASSWORD"] or ""
    database = env_vars["MYSQL_DATABASE"] or "hackathon"
    port = 3306  # Default MySQL port (Cloud SQL Proxy uses this)
    
    print(f"  Attempting connection with:")
    print(f"    Host: {host}")
    print(f"    Port: {port}")
    print(f"    User: {user}")
    print(f"    Database: {database}")
    print(f"    Password: {'SET' if password else 'NOT SET'}")
    print()
    
    # Try to connect
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10
        )
        print("  ✓ Connection successful!")
        
        # Test a simple query
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION(), USER(), DATABASE()")
            result = cursor.fetchone()
            print(f"  MySQL Version: {result[0]}")
            print(f"  Connected as: {result[1]}")
            print(f"  Current database: {result[2]}")
        
        connection.close()
        
    except pymysql.err.OperationalError as e:
        error_code, error_msg = e.args
        print(f"  ✗ Connection failed!")
        print(f"  Error code: {error_code}")
        print(f"  Error message: {error_msg}")
        print()
        print("  Common issues:")
        print("    - Wrong username (should be database user, not system user)")
        print("    - Wrong password")
        print("    - User doesn't exist in Cloud SQL")
        print("    - Cloud SQL Proxy not running")
        print("    - Wrong port (should be 3306 for proxy)")
        print()
        print("  Solutions:")
        print("    1. Check your .env file has correct MYSQL_USER and MYSQL_PWD")
        print("    2. Verify the user exists in Cloud SQL:")
        print("       gcloud sql users list --instance=uttc")
        print("    3. Make sure Cloud SQL Proxy is running")
        print("    4. Verify you're connecting to the right port")
        
except ImportError:
    print("  ⚠ pymysql not installed. Install with: pip install pymysql")
except Exception as e:
    print(f"  ⚠ Unexpected error: {e}")

print()
print("=" * 80)
print("Debug Complete")
print("=" * 80)

