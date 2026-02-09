#!/usr/bin/env python
"""
Utility script to generate secure values for deployment
"""
import secrets
import argparse

def generate_secret_key(length=32):
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(length)

def generate_database_url(user='postgres', password='', host='localhost', port=5432, db='todo_db'):
    """Generate a PostgreSQL connection string"""
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@{host}:{port}/{db}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate deployment configuration values')
    parser.add_argument('--secret-key', action='store_true', help='Generate SECRET_KEY')
    parser.add_argument('--db-url', action='store_true', help='Generate example DATABASE_URL')
    parser.add_argument('--all', action='store_true', help='Generate all values')
    
    args = parser.parse_args()
    
    if args.secret_key or args.all:
        print(f"SECRET_KEY={generate_secret_key()}")
    
    if args.db_url or args.all:
        print(f"\nExample DATABASE_URL for local development:")
        print(f"DATABASE_URL=postgresql://postgres:password@localhost:5432/todo_db")
        print(f"\nFor Render.com, use their provided connection string")
    
    if not any([args.secret_key, args.db_url, args.all]):
        print("Usage: python generate_config.py --secret-key --db-url --all")
        print("\nExample:")
        print("  python generate_config.py --all")
