#!/usr/bin/env python3
"""
Quick Start Helper for Mercari Dataset Import
This script helps you get started quickly by checking prerequisites and guiding setup.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_venv():
    """Check if virtual environment exists"""
    venv_path = "venv"
    if os.path.exists(venv_path):
        print(f"✓ Virtual environment found at {venv_path}")
        return True
    print(f"❌ Virtual environment not found")
    return False

def check_env_file():
    """Check if .env file exists"""
    if os.path.exists(".env"):
        print("✓ .env file found")
        return True
    print("❌ .env file not found")
    return False

def check_mysql_connection():
    """Check if MySQL is accessible"""
    try:
        import pymysql
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", "3306"))
        user = os.getenv("MYSQL_USER")
        password = os.getenv("MYSQL_PASSWORD")
        
        if not user or not password:
            print("❌ MySQL credentials not set in .env")
            return False
            
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        conn.close()
        print(f"✓ MySQL connection successful ({host}:{port})")
        return True
    except ImportError:
        print("⚠️  pymysql not installed (will be installed)")
        return None
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return False

def print_header():
    """Print welcome header"""
    print("\n" + "="*80)
    print("🚀 MERCARI DATASET IMPORT - QUICK START")
    print("="*80)
    print("\nThis script will help you set up everything needed to import")
    print("the Mercari dataset into your MySQL or Cloud SQL database.\n")

def print_section(title):
    """Print section header"""
    print(f"\n{'─'*80}")
    print(f"📋 {title}")
    print(f"{'─'*80}")

def main():
    print_header()
    
    # Check prerequisites
    print_section("Checking Prerequisites")
    
    python_ok = check_python_version()
    venv_exists = check_venv()
    env_exists = check_env_file()
    
    if not python_ok:
        print("\n❌ Please install Python 3.8 or higher")
        return
    
    # Setup instructions
    print_section("Setup Instructions")
    
    if not venv_exists:
        print("\n1️⃣  Create a virtual environment:")
        print("   python3 -m venv venv")
        print("\n2️⃣  Activate it:")
        print("   source venv/bin/activate")
        print("\n3️⃣  Install dependencies:")
        print("   pip install -r requirements_merrec.txt")
    else:
        print("\n1️⃣  Activate the virtual environment:")
        print("   source venv/bin/activate")
        print("\n2️⃣  Install/update dependencies:")
        print("   pip install -r requirements_merrec.txt")
    
    if not env_exists:
        print("\n3️⃣  Create a .env file with your database credentials:")
        print("   cat > .env << EOF")
        print("   DB_HOST=localhost")
        print("   DB_PORT=3306")
        print("   MYSQL_USER=root")
        print("   MYSQL_PASSWORD=your-password")
        print("   MYSQL_DATABASE=mercari_db")
        print("   EOF")
    
    # Usage examples
    print_section("Usage Examples")
    
    print("\n📊 1. Explore the dataset first:")
    print("   python explore_merrec.py")
    
    print("\n💾 2. Import to local MySQL:")
    print("   python import_merrec_local.py --limit 1000 --verify")
    
    print("\n☁️  3. Import to Cloud SQL:")
    print("   # First, add CLOUD_SQL_INSTANCE to your .env file")
    print("   python import_merrec_to_cloudsql.py --limit 1000 --verify")
    
    # Next steps
    print_section("Next Steps")
    
    steps = []
    if not venv_exists:
        steps.append("Create and activate virtual environment")
    if not env_exists:
        steps.append("Create .env file with database credentials")
    steps.append("Install dependencies: pip install -r requirements_merrec.txt")
    steps.append("Explore the dataset: python explore_merrec.py")
    steps.append("Start import: python import_merrec_local.py --limit 1000 --verify")
    
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    
    print_section("Documentation")
    print("\n📚 For detailed instructions, see:")
    print("   MERREC_IMPORT_README.md")
    
    print("\n" + "="*80)
    print("💡 Tip: Start with a small limit (1000 rows) to test everything works!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

