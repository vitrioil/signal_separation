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
    SeparatedSignal,
)
from api.services import (
    create_signal,
    create_stem,
    read_signal,
    remove_signal,
    save_signal_file,
    read_signal_file,
    save_stem_file,
    update_signal,
    get_stem_id,
    read_one_signal,
    delete_signal_file,
)
from api.separator import Separator
from api.db import get_database
from api.utils.signal import split_audio, process_signal, get_separator

router = APIRouter(
    prefix="/signal",
    tags=["signal"],
    responses={404: {"description": "Not found"}},
)


async def signal_separation_task(
    separator: Separator, db: AsyncIOMotorClient, signal: Signal
):
    # mem expensive
    stream = await read_signal_file(
        db, signal.signal_metadata.filename, stream=False
    )
    separated_signals = split_audio(
        separator,
        stream,
        signal.signal_metadata.extension,
        signal.signal_metadata.signal_type,
    )

    separated_stems = []
    separated_stem_id = []
    for stem_name, separate_signal in separated_signals.items():
        stem_file_id = get_stem_id(stem_name, signal.signal_id)
        stem_id = await save_stem_file(db, stem_file_id, separate_signal)

        separated_stems.append(stem_name)
        separated_stem_id.append(stem_id)
        stem = SeparatedSignal(
            signal_id=stem_id,
            signal_metadata=signal.signal_metadata,
            stem_name=stem_name,
        )

        await create_stem(db, stem)
    # store signal stem ids in original signal
    await update_signal(
        db,
        signal.signal_id,
        separated_stems=separated_stems,
        separated_stem_id=separated_stem_id,
    )


@router.get("/", response_model=List[SignalInResponse])
async def get_signal(db: AsyncIOMotorClient = Depends(get_database)):
    signals = await read_signal(db)
    signals = list(map(lambda x: SignalInResponse(signal=x), signals))
    return signals


@router.get("/stem/{signal_id}/{stem}")
async def get_stem(
    signal_id: str, stem: str, db: AsyncIOMotorClient = Depends(get_database)
):
    stem_file_id = get_stem_id(stem, signal_id)
    stream = await read_signal_file(db, stem_file_id)
    if not stream:
        return HTTPException(status_code=404, detail="Stem not found")
    return StreamingResponse(stream)


@router.post(
    "/{signal_type}",
    response_model=SignalInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_signal(
    background_task: BackgroundTasks,
    separator_type: dict = Depends(get_separator),
    db: AsyncIOMotorClient = Depends(get_database),
    signal_file: UploadFile = File(...),
):
    # early validations for file extension / metadata based validation
    separator, signal_type = (
        separator_type.get("separator"),
        separator_type.get("signal_type"),
    )
    try:
        signal_metadata = process_signal(signal_file, signal_type)
    except Exception:
        return HTTPException(
            status_code=404, detail="Error while processing file"
        )
    file_id = await save_signal_file(db, signal_file)
    signal = SignalInCreate(signal_metadata=signal_metadata, signal_id=file_id)
    signal_in_db = await create_signal(db, signal)
    background_task.add_task(
        signal_separation_task, separator, db, signal_in_db
    )
    return SignalInResponse(signal=signal_in_db)


@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: str, db: AsyncIOMotorClient = Depends(get_database)
):
    signal = await read_one_signal(db, signal_id)
    if not signal:
        return HTTPException(status_code=404, detail="Signal does not exist")

    stem_ids = signal.separated_stem_id

    # Delete stem files and from collection
    for stem_id in stem_ids:
        await delete_signal_file(db, stem_id)
        deleted = await remove_signal(db, stem_id, stem=True)

    # Delete signal file and from collection
    await delete_signal_file(db, signal_id)
    deleted = await remove_signal(db, signal_id)
    return {"signal_id": signal_id, "deleted": deleted}
