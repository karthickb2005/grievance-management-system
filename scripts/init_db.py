"""
Database initialization script for Grievance Router.
Creates SQLite database and tables.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app import models  # Import all models

def init_db():
    """Initialize database with all tables."""
    print("Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully!")
    print(f"Database: {engine.url}")

if __name__ == "__main__":
    init_db()