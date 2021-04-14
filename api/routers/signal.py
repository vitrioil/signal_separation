import itertools
from typing import List
from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Depends,
    BackgroundTasks,
)
from motor.motor_asyncio import AsyncIOMotorClient

from api.schemas import (
    Signal,
    SignalMetadata,
    SignalInResponse,
    SignalInCreate,
    SeparatedSignal,
    SeparatedSignalInResponse,
)
from api.services import (
    create_signal,
    create_stem,
    read_signal,
    remove_signal,
    save_signal_file,
    read_signal_file,
    save_stem_file,
)
from api.separator import SignalType
from api.db import get_database
from api.utils.signal import split_audio, process_signal

router = APIRouter(
    prefix="/signal",
    tags=["signal"],
    responses={404: {"description": "Not found"}},
)


async def signal_separation_task(db: AsyncIOMotorClient, signal: Signal):
    # mem expensive
    stream = await read_signal_file(
        db, signal.signal_metadata.filename, stream=False
    )
    separated_signals = split_audio(
        stream,
        signal.signal_metadata.extension,
        signal.signal_metadata.signal_type,
    )

    for stem_name, separate_signal in separated_signals.items():
        stem_file_name = f"{stem_name}__{signal.signal_metadata.filename}"
        stem_id = await save_stem_file(db, stem_file_name, separate_signal)
        stem = SeparatedSignal(
            signal_id=stem_id,
            signal_metadata=signal.signal_metadata,
            stem_name=stem_name,
        )
        await create_stem(db, stem)


@router.get("/", response_model=List[Signal])
async def get_signal(db: AsyncIOMotorClient = Depends(get_database)):
    signals = await read_signal(db)
    return signals


@router.get("/stem/{filename}/{stem}")
async def get_stem(
    filename: str, stem: str, db: AsyncIOMotorClient = Depends(get_database)
):
    stem_file_name = f"{stem}__{filename}"
    stream = await read_signal_file(db, stem_file_name)
    if not stream:
        return HTTPException(status_code=404, detail="Stem not found")
    return StreamingResponse(stream)


@router.get("/test_binary/{filename}")
async def get_signal_file(
    filename: str, db: AsyncIOMotorClient = Depends(get_database)
):
    stream = await read_signal_file(db, filename)
    if not stream:
        return HTTPException(status_code=404, detail="File not found")
    return StreamingResponse(stream)


@router.post("/{signal_type}", response_model=SignalInResponse)
async def post_signal(
    signal_type: SignalType,
    background_task: BackgroundTasks,
    db: AsyncIOMotorClient = Depends(get_database),
    signal_file: UploadFile = File(...),
):
    # early validations for file extension / metadata based validation
    try:
        signal_metadata = process_signal(signal_file, signal_type)
    except Exception as e:
        return HTTPException(
            status_code=404, detail="Error while processing file"
        )
    file_id = await save_signal_file(db, signal_file)
    signal = SignalInCreate(signal_metadata=signal_metadata, signal_id=file_id)
    signal_in_db = await create_signal(db, signal)
    background_task.add_task(signal_separation_task, db, signal_in_db)
    return SignalInResponse(signal=signal_in_db)


@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: str, db: AsyncIOMotorClient = Depends(get_database)
):
    deleted = await remove_signal(db, signal_id)
    return {"signal_id": signal_id, "deleted": deleted}
