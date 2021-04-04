from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

from api.schemas import SignalInResponse, Signal, SignalInDB
from api.config import database_name, signal_collection_name, stem_collection_name


async def create_signal(conn: AsyncIOMotorClient, signal: Signal):
    signal_in_db = SignalInDB(**signal.dict())
    row = (
        await conn.get_default_database()
        .get_collection(signal_collection_name)
        .insert_one(signal.dict())
    )

    signal_in_db.id = row.inserted_id
    signal_in_db.created_at = ObjectId(signal_in_db.id).generation_time
    signal_in_db.updated_at = ObjectId(signal_in_db.id).generation_time

    return signal_in_db
