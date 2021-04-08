from typing import List
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from api.schemas import (
    Signal,
    SignalType,
    SignalMetadata,
    SignalInResponse,
    SignalInCreate,
)
from api.services import create_signal, read_signal, remove_signal
from api.db import get_database

router = APIRouter(
    prefix="/signal", tags=["signal"], responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=List[Signal])
async def get_signal(db: AsyncIOMotorClient = Depends(get_database)):
    signals = await read_signal(db)
    return signals


@router.post("/{signal_type}", response_model=SignalInResponse)
async def post_signal(
    signal_type: SignalType, db: AsyncIOMotorClient = Depends(get_database)
):
    signal_metadata = SignalMetadata(
        extension="mp3",
        sample_rate=42_000,
        length=60,
        channels=2,
        signal_type=signal_type,
    )
    signal = SignalInCreate(signal_metadata=signal_metadata, signal_id="TEST")
    signal_in_response = await create_signal(db, signal)
    return SignalInResponse(signal=signal_in_response)


@router.delete("/{signal_id}")
async def delete_signal(signal_id: str, db: AsyncIOMotorClient = Depends(get_database)):
    deleted = await remove_signal(db, signal_id)
    return {"signal_id": signal_id, "deleted": deleted}


# @router.get("/{signal_type}", response_model=Signal)
# async def read_signal(signal_type: SignalType):
#     signal = list(
#         filter(lambda x: x["signal_metadata"]["signal_type"] == signal_type, signal_db)
#     )
#     if not signal:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return signal[0]


# @router.put(
#     "/{signal_type}", responses={403: {"description": "Operation forbidden"}},
# )
# async def update_signal(signal_type: SignalType, updated_signal: Signal):
#     if signal_type != SignalType.Music:
#         raise HTTPException(
#             status_code=403, detail="You can only update the item: Music"
#         )
#     return signal_db[0]


# @router.post("/create")
# async def post_signal_test(file: UploadFile = File(...)):
#     return {"file_name": file.filename}
