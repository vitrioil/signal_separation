from typing import List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from bson.objectid import ObjectId
from fastapi import UploadFile
from gridfs.errors import NoFile

from api.schemas import SignalInResponse, Signal, SignalInDB, SeparatedSignal
from api.config import database_name, signal_collection_name, stem_collection_name


async def create_signal(conn: AsyncIOMotorClient, signal: Signal):
    signal_in_db = SignalInDB(**signal.dict())
    row = (
        await conn.get_default_database()
        .get_collection(signal_collection_name)
        .insert_one(signal.dict())
    )

    signal_in_db.id = str(row.inserted_id)
    signal_in_db.created_at = ObjectId(signal_in_db.id).generation_time
    signal_in_db.updated_at = ObjectId(signal_in_db.id).generation_time

    return signal_in_db


async def save_signal_file(
    conn: AsyncIOMotorClient, signal_file: UploadFile
):
    db = conn.get_default_database()
    fs = AsyncIOMotorGridFSBucket(db)
    file_id = await fs.upload_from_stream(
        signal_file.filename,
        signal_file.file,
        metadata={"contentType": signal_file.content_type},
    )
    signal_id = str(file_id)
    return signal_id


async def read_signal_file(
    conn: AsyncIOMotorClient, filename: str
):
    db = conn.get_default_database()
    fs = AsyncIOMotorGridFSBucket(db)
    try:
        grid_out = await fs.open_download_stream_by_name(filename)
    except NoFile:
        return None
    return chunk_gen(grid_out)


async def chunk_gen(grid_out):
    while True:
        chunk = await grid_out.readchunk()
        if not chunk:
            return
        yield chunk


async def read_one_signal(conn: AsyncIOMotorClient, signal_id: str):
    pass


async def read_signal(conn: AsyncIOMotorClient, length: int = 20):
    rows = (
        await conn.get_default_database()
        .get_collection(signal_collection_name)
        .find()
        .to_list(length=length)
    )
    rows = list(map(lambda x: Signal(**x), rows))
    return rows


async def remove_signal(conn: AsyncIOMotorClient, signal_id: str):
    rows = (
        await conn.get_default_database()
        .get_collection(signal_collection_name)
        .delete_one({"signal_id": signal_id})
    )
    return rows.deleted_count == 1


async def save_stem(conn: AsyncIOMotorClient, signal_id: str, stems: List[SeparatedSignal])
    pass
