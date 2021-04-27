import numpy as np
import librosa
from datetime import datetime
from tempfile import NamedTemporaryFile
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from bson.objectid import ObjectId
from fastapi import UploadFile
from gridfs.errors import NoFile

from api.schemas import (
    Signal,
    SignalInDB,
    SeparatedSignal,
    SeparatedSignalInDB,
    SignalState,
)
from api.config import (
    signal_collection_name,
    stem_collection_name,
    grid_bucket_name,
    signal_state_collection_name,
)


def get_stem_id(stem_name: str, signal_id: str):
    return f"{stem_name}__{signal_id}"


async def read_one_signal(conn: AsyncIOMotorClient, signal_id: str):
    row = (
        await conn.get_default_database()
        .get_collection(signal_collection_name)
        .find_one({"signal_id": signal_id})
    )
    if row:
        row = SignalInDB(**row)
    return row


async def read_signal(conn: AsyncIOMotorClient, length: int = 20):
    rows = (
        await conn.get_default_database()
        .get_collection(signal_collection_name)
        .find()
        .to_list(length=length)
    )
    rows = list(map(lambda x: SignalInDB(**x), rows))
    return rows


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


async def update_signal(
    conn: AsyncIOMotorClient, signal_id: str, **update_kwargs
):
    signal = await read_one_signal(conn, signal_id)

    signal = signal.dict()
    signal = SignalInDB(**{**signal, **update_kwargs})
    signal.updated_at = datetime.now()
    await conn.get_default_database().get_collection(
        signal_collection_name
    ).replace_one({"signal_id": signal_id}, signal.dict())
    return signal


async def remove_signal(conn: AsyncIOMotorClient, signal_id: str, stem=False):
    collection_name = signal_collection_name
    if stem:
        collection_name = stem_collection_name
    rows = (
        await conn.get_default_database()
        .get_collection(collection_name)
        .delete_one({"signal_id": signal_id})
    )
    return rows.deleted_count == 1


async def create_stem(conn: AsyncIOMotorClient, signal: SeparatedSignal):
    signal_in_db = SeparatedSignalInDB(**signal.dict())
    row = (
        await conn.get_default_database()
        .get_collection(stem_collection_name)
        .insert_one(signal.dict())
    )

    signal_in_db.id = str(row.inserted_id)
    signal_in_db.created_at = ObjectId(signal_in_db.id).generation_time
    signal_in_db.updated_at = ObjectId(signal_in_db.id).generation_time

    return signal_in_db


async def save_signal_file(conn: AsyncIOMotorClient, signal_file: UploadFile):
    db = conn.get_default_database()
    fs = AsyncIOMotorGridFSBucket(db, bucket_name=grid_bucket_name)
    signal_file.file.seek(0)
    file_id = await fs.upload_from_stream(
        signal_file.filename,
        signal_file.file,
        metadata={"contentType": signal_file.content_type},
    )
    signal_id = str(file_id)
    return signal_id


async def save_stem_file(
    conn: AsyncIOMotorClient,
    stem_name: str,
    signal: np.ndarray,
    sample_rate: int,
):
    db = conn.get_default_database()
    fs = AsyncIOMotorGridFSBucket(db, bucket_name=grid_bucket_name)
    with NamedTemporaryFile() as temp_file:
        filename = temp_file.name
        librosa.output.write_wav(
            filename, np.asfortranarray(signal), sr=sample_rate
        )
        file_id = await fs.upload_from_stream(stem_name, temp_file)
    stem_id = str(file_id)
    return stem_id


async def read_signal_file(
    conn: AsyncIOMotorClient, filename: str, stream=True
):
    db = conn.get_default_database()
    fs = AsyncIOMotorGridFSBucket(db, bucket_name=grid_bucket_name)
    try:
        grid_out = await fs.open_download_stream_by_name(filename)
    except NoFile:
        return None
    if stream:
        return chunk_gen(grid_out)
    file_content = await grid_out.read()
    return file_content


async def chunk_gen(grid_out):
    while True:
        chunk = await grid_out.readchunk()
        if not chunk:
            return
        yield chunk


async def delete_signal_file(conn: AsyncIOMotorClient, file_id: str):
    db = conn.get_default_database()
    fs = AsyncIOMotorGridFSBucket(db, bucket_name=grid_bucket_name)
    try:
        await fs.delete(ObjectId(file_id))
    except NoFile:
        raise Exception("No File found")


async def get_signal_state(conn: AsyncIOMotorClient, signal_id: str):
    row = (
        await conn.get_default_database()
        .get_collection(signal_state_collection_name)
        .find_one({"signal_id": signal_id})
    )
    print(row)
    if row:
        signal_state = SignalState(**row)
        return signal_state


async def update_signal_state(
    conn: AsyncIOMotorClient, signal_id: str, state: str
):
    signal_state = SignalState(signal_id=signal_id, signal_state=state)
    print(signal_state)
    row = (
        await conn.get_default_database()
        .get_collection(signal_state_collection_name)
        .update_one(
            {"signal_id": signal_id},
            {"$set": {"signal_state": signal_state.signal_state}},
            upsert=True,
        )
    )
    if row:
        return signal_state


async def watch_collection_field(
    conn: AsyncIOMotorClient, field: str, field_name: str = "signal_id"
):
    collection = conn.get_default_database().get_collection(
        signal_state_collection_name
    )

    pipeline = [
        {
            "$match": {
                "$and": [
                    {
                        "operationType": {
                            "$in": ["insert", "update", "replace"]
                        },
                        f"fullDocument.{field_name}": field,
                    }
                ]
            }
        }
    ]
    async with collection.watch(
        pipeline=pipeline, full_document="updateLookup"
    ) as change_stream:
        async for change in change_stream:
            data = change["updateDescription"]["updatedFields"]
            yield data
