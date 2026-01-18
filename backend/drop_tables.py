"""
Drop all tables and recreate
"""
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.db.database import Base, engine

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("All tables dropped!")

print("\nRecreating all tables...")
Base.metadata.create_all(bind=engine)
print("All tables created!")
