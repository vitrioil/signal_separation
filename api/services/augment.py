from motor.motor_asyncio import AsyncIOMotorClient

from api.config import augment_collection_name
from api.schemas import BaseAugment


async def create_augmentation(
    conn: AsyncIOMotorClient, augmentation: BaseAugment
):
    row = (
        await conn.get_default_database()
        .get_collection(augment_collection_name)
        .insert_one(augmentation.dict())
    )
    if row:
        return True
