from sqlalchemy import create_engine
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()

def init_db():
    """Initialize the database with all tables"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/fire_safety_suite")
    engine = create_engine(DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()