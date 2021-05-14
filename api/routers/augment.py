from typing import Coroutine, List
from fastapi import APIRouter

from api.schemas.augment import AugmentType

router = APIRouter(prefix="/augment", tags=["augment"])


@router.get("/")
async def augmentations() -> Coroutine[List[str], None, None]:
    return [augment.value for augment in AugmentType]
