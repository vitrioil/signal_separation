from motor.motor_asyncio import AsyncIOMotorClient

from api.config import augment_collection_name
from api.schemas import BaseAugment, Copy, Volume


async def create_augmentation(
    conn: AsyncIOMotorClient, augmentation: BaseAugment
):
    pass
