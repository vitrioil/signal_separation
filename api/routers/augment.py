from os import stat
from typing import Coroutine, List, Union
from fastapi import APIRouter, status, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.responses import StreamingResponse

from api.dependencies import get_current_user
from api.db import get_database
from api.schemas import Augmentation, User, Copy, Volume, signal
from api.utils.augment import augment_signal
from api.services import validate_user_signal, get_stem_id


router = APIRouter(prefix="/augment", tags=["augment"])


@router.get("/")
async def augmentations() -> Coroutine[List[str], None, None]:
    return [augment.value for augment in Augmentation]


@router.post("/augment/", status_code=status.HTTP_202_ACCEPTED)
async def volume(
    augmentation: List[Union[Volume, Copy]],
    db: AsyncIOMotorClient = Depends(get_database),
    user: User = Depends(get_current_user),
) -> Coroutine[StreamingResponse, None, None]:
    if len(augmentation) == 0:
        raise HTTPException(status_code=400, detail="Empty augmentation not allowed")
    signal_id = augmentation[0].signal_id
    if any(signal_id != aug.signal_id for aug in augmentation):
        raise HTTPException(status_code=400, detail="Augment one signal at a time")
    if not await validate_user_signal(db, signal_id, user.username):
        raise HTTPException(status_code=400, detail="Signal not found")

    signals = {}
    for augment in augmentation:
        stem_augments = signals.get(augment.signal_stem, [])
        stem_augments.append(augment)
        signals[augment.signal_stem] = stem_augments
    
    for stem, augmentations in signals.items():
        # TODO: get signal stem in tensor
        result = augment_signal("signal_stem_in_tensor", augmentations)