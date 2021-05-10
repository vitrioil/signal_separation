from motor.motor_asyncio import AsyncIOMotorClient

from api.db import db
from api.config import MONGODB_URL


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGODB_URL)


async def close_mongo_connection():
    db.client.close()
