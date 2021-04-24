from typing import List
from fastapi.responses import StreamingResponse
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Depends,
    BackgroundTasks,
    status,
)
from motor.motor_asyncio import AsyncIOMotorClient

from api.schemas import (
    Signal,
    SignalInResponse,
    SignalInCreate,
)
from api.services import (
    create_signal,
    read_signal,
    remove_signal,
    save_signal_file,
    read_signal_file,
    get_stem_id,
    read_one_signal,
    delete_signal_file,
)
from api.separator import SignalType
from api.db import get_database
from api.utils.signal import process_signal
from api.worker import separate

router = APIRouter(
    prefix="/signal",
    tags=["signal"],
    responses={404: {"description": "Not found"}},
)


async def signal_separation_task(signal: Signal):
    separate.apply_async((signal.dict(),))


@router.get(
    "/", response_model=List[SignalInResponse], status_code=status.HTTP_200_OK
)
async def get_signal(db: AsyncIOMotorClient = Depends(get_database)):
    signals = await read_signal(db)
    signals = list(map(lambda x: SignalInResponse(signal=x), signals))
    return signals


@router.get("/stem/status/{signal_id}")
async def get_stem_processing_status(
    # websocket: WebSocket,
    signal_id: str,
    db: AsyncIOMotorClient = Depends(get_database),
):
    pass


@router.get("/stem/{signal_id}/{stem}", status_code=status.HTTP_200_OK)
async def get_stem(
    signal_id: str, stem: str, db: AsyncIOMotorClient = Depends(get_database)
):
    stem_file_id = get_stem_id(stem, signal_id)
    stream = await read_signal_file(db, stem_file_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stem not found")
    return StreamingResponse(stream, media_type="audio/mpeg")


@router.post(
    "/{signal_type}",
    response_model=SignalInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_signal(
    background_task: BackgroundTasks,
    signal_type: SignalType,
    # separator_type: dict = Depends(get_separator),
    db: AsyncIOMotorClient = Depends(get_database),
    signal_file: UploadFile = File(...),
):
    # early validations for file extension / metadata based validation
    # separator, signal_type = (
    #     separator_type.get("separator"),
    #     separator_type.get("signal_type"),
    # )
    try:
        signal_metadata = process_signal(signal_file, signal_type)
    except Exception:
        raise HTTPException(
            status_code=404, detail="Error while processing file"
        )
    file_id = await save_signal_file(db, signal_file)
    signal = SignalInCreate(signal_metadata=signal_metadata, signal_id=file_id)
    signal_in_db = await create_signal(db, signal)
    background_task.add_task(signal_separation_task, signal_in_db)
    return SignalInResponse(signal=signal_in_db)


@router.delete("/{signal_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_signal(
    signal_id: str, db: AsyncIOMotorClient = Depends(get_database)
):
    signal = await read_one_signal(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal does not exist")

    stem_ids = signal.separated_stem_id

    # Delete stem files and from collection
    for stem_id in stem_ids:
        await delete_signal_file(db, stem_id)
        deleted = await remove_signal(db, stem_id, stem=True)

    # Delete signal file and from collection
    await delete_signal_file(db, signal_id)
    deleted = await remove_signal(db, signal_id)
    return {"signal_id": signal_id, "deleted": deleted}
