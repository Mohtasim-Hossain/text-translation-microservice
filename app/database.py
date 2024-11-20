from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

UPLOADS_DIR = "uploads"
DOWNLOADS_DIR = "downloads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Get the MongoDB URI from environment variables
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize the Async MongoDB client
client = AsyncIOMotorClient(MONGODB_URI)
db = client.translation_service
history_collection = db.session_history

async def startup_db():
    # Test connection on startup
    try:
        # Ping the database to check if it's working
        await db.command("ping")
        print("Successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")


