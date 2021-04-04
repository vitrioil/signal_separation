from typing import List
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from api.schemas import Signal, SignalType, SignalMetadata, SignalInResponse, SignalInCreate
from api.services import create_signal
from api.db import get_database

router = APIRouter(
    prefix="/signal", tags=["signal"], responses={404: {"description": "Not found"}}
)

signal_db: List = [
    {
        "signal_metadata": {
            "extension": "mp3",
            "sample_rate": 42000,
            "length": 60,
            "channels": 2,
            "signal_type": SignalType.Music,
        }
    }
]


@router.get("/", response_model=List[Signal])
async def read_signal_names():
    return signal_db


@router.post("/", response_model=SignalInResponse)
async def post_signal(signal_type: SignalType, db: AsyncIOMotorClient = Depends(get_database)):
    signal_metadata = SignalMetadata(extension="mp3", sample_rate=42_000,
                                     length=60, channels=2, signal_type=signal_type)
    signal = SignalInCreate(signal_metadata=signal_metadata, signal_id="TEST")
    signal_in_response = await create_signal(db, signal)
    return SignalInResponse(signal=signal_in_response)


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
