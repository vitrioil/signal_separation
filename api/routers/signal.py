from typing import List, Coroutine
from fastapi.responses import StreamingResponse
from fastapi import (
    # Request,
    Path,
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Depends,
    BackgroundTasks,
    status,
    WebSocket,
)
from motor.motor_asyncio import AsyncIOMotorClient

# from sse_starlette.sse import EventSourceResponse

from api.schemas import (
    SignalInResponse,
    SignalInCreate,
    SignalState,
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
    get_signal_state,
    watch_collection_field,
    update_signal_state,
)
from api.separator import SignalType
from api.db import get_database
from api.utils.signal import process_signal
from api.worker import separate, TaskState

router = APIRouter(
    prefix="/signal",
    tags=["signal"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=List[SignalInResponse],
    status_code=status.HTTP_200_OK,
    name="get_signal",
)
async def get_signal(
    db: AsyncIOMotorClient = Depends(get_database),
) -> Coroutine[List[SignalInResponse], None, None]:
    """Get all signals that were posted.
    """
    signals = await read_signal(db)
    signals = list(map(lambda x: SignalInResponse(signal=x), signals))
    return signals


@router.get(
    "/state/{signal_id}",
    response_model=SignalState,
    status_code=status.HTTP_200_OK,
)
async def get_stem_state(
    signal_id: str = Path(..., title="Signal ID"),
    db: AsyncIOMotorClient = Depends(get_database),
) -> Coroutine[SignalState, None, None]:
    """Get state of the signal separation process
    """
    signal_state = await get_signal_state(db, signal_id)
    if not signal_state:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal_state


@router.websocket("/status/{signal_id}")
async def get_stem_processing_status(
    websocket: WebSocket,
    signal_id: str = Path(..., title="Signal ID"),
    db: AsyncIOMotorClient = Depends(get_database),
):
    """Open a WebSocket connection to receive
    state updates of the background process.
    """
    await websocket.accept()

    signal_state = await get_signal_state(db, signal_id)
    if signal_state and signal_state.signal_state == TaskState.Complete:
        await websocket.send_text(signal_state.signal_state)
        await websocket.close()
        return

    async for stream in watch_collection_field(db, signal_id):
        state = stream["signal_state"]
        await websocket.send_text(state)
    await websocket.close()


# @router.get("/state/{signal_id}")
# async def get_state(
#     request: Request, signal_id: str,
# db: AsyncIOMotorClient = Depends(get_database)
# ):
#     def _filter(req):
#         event_gen = watch_collection_field(db, sig, request=request)
#     return EventSourceResponse(_filter())


@router.get("/stem/{signal_id}/{stem}", status_code=status.HTTP_200_OK)
async def get_stem(
    signal_id: str = Path(..., title="Signal ID"),
    stem: str = Path(..., title="Stem name of separated signal"),
    db: AsyncIOMotorClient = Depends(get_database),
) -> Coroutine[StreamingResponse, None, None]:
    """Get an individual separated signal stem.
    """
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
    signal_type: SignalType = Path(..., title="Type of Signal"),
    db: AsyncIOMotorClient = Depends(get_database),
    signal_file: UploadFile = File(...),
) -> Coroutine[SignalInResponse, None, None]:
    """Post a signal to separate. Signal Type is used to
    determine the separation process. Posting triggers a
    background process which can be tracked by `/signal/state`
    or `/signal/status`.
    """
    # early validations for file extension / metadata based validation
    try:
        signal_metadata = process_signal(signal_file, signal_type)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Error while processing file"
        )
    file_id = await save_signal_file(db, signal_file)
    signal = SignalInCreate(signal_metadata=signal_metadata, signal_id=file_id)
    signal_in_db = await create_signal(db, signal)
    separate.delay(signal_in_db.dict())
    return SignalInResponse(signal=signal_in_db)


@router.delete("/{signal_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_signal(
    signal_id: str = Path(..., title="Signal ID"),
    db: AsyncIOMotorClient = Depends(get_database),
) -> Coroutine[dict, None, None]:
    """Delete a signal.
    """
    signal = await read_one_signal(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    stem_ids = signal.separated_stem_id

    # Delete stem files and from collection
    for stem_id in stem_ids:
        try:
            await delete_signal_file(db, stem_id)
        except Exception:
            raise HTTPException(status_code=500, detail="Internal error")
        deleted = await remove_signal(db, stem_id, stem=True)

    # Delete signal file and from collection
    try:
        await delete_signal_file(db, signal_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    deleted = await remove_signal(db, signal_id)
    if deleted:
        await update_signal_state(
            db,
            SignalState(signal_id=signal_id, signal_state=TaskState.Deleted),
        )
    return {"signal_id": signal_id, "deleted": deleted}
