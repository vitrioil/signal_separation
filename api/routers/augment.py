from api.utils.signal import read_audio
from api.services.signal import (
    read_one_signal,
    read_signal_file,
    save_stem_file,
    update_stem,
)
from typing import Coroutine, List, Union
from fastapi import APIRouter, status, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.responses import StreamingResponse

from api.dependencies import get_current_user
from api.db import get_database
from api.schemas import Augmentation, User, Copy, Volume, Reverb
from api.utils.augment import augment_signal
from api.services import get_stem_id


router = APIRouter(prefix="/augment", tags=["augment"])


@router.get("/types")
async def augmentations() -> Coroutine[List[str], None, None]:
    return [augment.value for augment in Augmentation]


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def augment(
    augmentation: List[Union[Volume, Copy, Reverb]],
    db: AsyncIOMotorClient = Depends(get_database),
    user: User = Depends(get_current_user),
) -> Coroutine[StreamingResponse, None, None]:
    if len(augmentation) == 0:
        raise HTTPException(
            status_code=400, detail="Empty augmentation not allowed"
        )
    signal_id = augmentation[0].signal_id
    if any(signal_id != aug.signal_id for aug in augmentation):
        raise HTTPException(
            status_code=400, detail="Augment one signal at a time"
        )
    signal = await read_one_signal(db, signal_id, user.username)
    if not signal:
        raise HTTPException(status_code=400, detail="Signal not found")

    signals = {}
    for augment in augmentation:
        stem_augments = signals.get(augment.signal_stem, [])
        stem_augments.append(augment)
        signals[augment.signal_stem] = stem_augments
    for stem, augmentations in signals.items():
        stem_id = get_stem_id(stem, signal_id)
        stem_signal = await read_signal_file(
            db, get_stem_id(stem, signal_id), stream=False
        )
        stem_signal = read_audio(stem_signal)
        result = augment_signal(
            stem_signal, augmentations, signal.signal_metadata.sample_rate
        )
        await save_stem_file(
            db,
            stem_id,
            result,
            signal.signal_metadata.sample_rate,
            augmented_signal=True,
        )
        await update_stem(
            db, signal.signal_id, stem, user.username, augmented=True
        )
    return True
