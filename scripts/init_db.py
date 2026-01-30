import sys
import os

# Add the parent directory to the path to allow importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import engine, Base
from app.config import load_config
from app import models  # Ensure models are registered with Base

def init_db():
    """Initializes the database by creating all tables defined in models.py."""
    load_config()
    print("Initializing database...")
    # This will create the tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete. Tables created.")

if __name__ == "__main__":
    init_db()
