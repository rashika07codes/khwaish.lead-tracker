import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./khwaish.db")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-local-dev")
    
    # Email (Gmail API preferred)
    GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET")
    GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")
    FROM_EMAIL = os.getenv("FROM_EMAIL")
    
    # WhatsApp Webhook
    MAKE_ZAPIER_WEBHOOK_URL = os.getenv("MAKE_ZAPIER_WEBHOOK_URL")
    
    # Application Base URL (used for reply links)
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

settings = Settings()

def load_config():
    """Function to ensure config is loaded when imported."""
    pass
