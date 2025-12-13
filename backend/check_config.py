
import os
import sys

# Add the current directory to sys.path so we can import app setup
sys.path.append(os.getcwd())

from app.config import settings

def check_config():
    db_url = settings.DATABASE_URL
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"DATABASE_URL from settings starts with: {db_url.split(':')[0]}")
    
    if "sqlite" in db_url:
        print("WARNING: Using SQLite. The .env file was NOT loaded or DATABASE_URL is not set in it.")
    elif "postgresql" in db_url:
        print("SUCCESS: Using PostgreSQL.")
        if "+asyncpg" not in db_url:
            print("WARNING: Missing '+asyncpg' driver in connection string. Connection might fail.")
    else:
        print(f"Unknown database type: {db_url}")

if __name__ == "__main__":
    check_config()
