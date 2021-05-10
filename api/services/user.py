from motor.motor_asyncio import AsyncIOMotorClient

from api.config import user_collection_name
from api.schemas import UserInCreate, UserInDB


async def create_user(
    conn: AsyncIOMotorClient, user: UserInCreate, hashed_password: str
):
    if await get_user(conn, user.username):
        return
    user_in_db = UserInDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    row = (
        await conn.get_default_database()
        .get_collection(user_collection_name)
        .insert_one(user_in_db.dict())
    )
    if row:
        return user_in_db


async def get_user(conn: AsyncIOMotorClient, username: str):
    row = (
        await conn.get_default_database()
        .get_collection(user_collection_name)
        .find_one({"username": username})
    )
    if row:
        row = UserInDB(**row)
        return row
