from fastapi import APIRouter

router = APIRouter(prefix="/augment", tags=["augment"])


@router.get("/")
async def read_augment():
    return [{"username": "Rick"}, {"username": "Morty"}]


@router.get("/me")
async def read_augment_me():
    return {"username": "fakecurrentuser"}


@router.get("/{username}")
async def read_augment_parameters(username: str):
    return {"username": username}
