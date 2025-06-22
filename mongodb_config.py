"""
MongoDB configuration for TeraBox Bot
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# MongoDB URI
MONGO_URI = "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority"

# Initialize MongoDB clients
async_client = AsyncIOMotorClient(MONGO_URI)
sync_client = MongoClient(MONGO_URI)

# Database
async_db = async_client.terabox_bot
sync_db = sync_client.terabox_bot

# Collections
users_collection = async_db.users
videos_collection = async_db.videos
downloads_collection = async_db.downloads
settings_collection = async_db.settings

# Sync collections for web server
users_sync = sync_db.users
videos_sync = sync_db.videos
downloads_sync = sync_db.downloads
settings_sync = sync_db.settings

class MongoUser:
    @staticmethod
    async def create_or_update(user_data):
        """Create or update user"""
        await users_collection.update_one(
            {"telegram_id": user_data["telegram_id"]},
            {"$set": {**user_data, "updated_at": datetime.utcnow()}},
            upsert=True
        )
    
    @staticmethod
    async def find_by_telegram_id(telegram_id):
        """Find user by Telegram ID"""
        return await users_collection.find_one({"telegram_id": telegram_id})
    
    @staticmethod
    def count():
        """Count total users (sync)"""
        return users_sync.count_documents({})

class MongoVideo:
    @staticmethod
    async def create(video_data):
        """Create new video record"""
        video_data["created_at"] = datetime.utcnow()
        video_data["updated_at"] = datetime.utcnow()
        result = await videos_collection.insert_one(video_data)
        return str(result.inserted_id)
    
    @staticmethod
    async def find_by_id(video_id):
        """Find video by ID"""
        from bson import ObjectId
        return await videos_collection.find_one({"_id": ObjectId(video_id)})
    
    @staticmethod
    async def find_by_user(user_id, limit=10):
        """Find videos by user ID"""
        cursor = videos_collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    @staticmethod
    def count():
        """Count total videos (sync)"""
        return videos_sync.count_documents({})
    
    @staticmethod
    def find_by_id_sync(video_id):
        """Find video by ID (sync)"""
        from bson import ObjectId
        return videos_sync.find_one({"_id": ObjectId(video_id)})

class MongoDownload:
    @staticmethod
    async def create(download_data):
        """Create download record"""
        download_data["created_at"] = datetime.utcnow()
        await downloads_collection.insert_one(download_data)
    
    @staticmethod
    def count():
        """Count total downloads (sync)"""
        return downloads_sync.count_documents({})
    
    @staticmethod
    def count_by_type(download_type):
        """Count downloads by type (sync)"""
        return downloads_sync.count_documents({"download_type": download_type})

async def init_mongodb():
    """Initialize MongoDB indexes"""
    try:
        # Create indexes
        await users_collection.create_index("telegram_id", unique=True)
        await videos_collection.create_index("user_id")
        await videos_collection.create_index("created_at")
        await downloads_collection.create_index("user_id")
        await downloads_collection.create_index("video_id")
        
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"MongoDB initialization error: {e}")