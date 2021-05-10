from fastapi import APIRouter, status, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from api.db import get_database
from api.schemas import UserInCreate, UserInResponse, User
from api.services import create_user


router = APIRouter(prefix="/user", tags=["user"])


@router.post("/register", response_model=UserInResponse)
async def register_user(
    user: UserInCreate, db: AsyncIOMotorClient = Depends(get_database)
):
    user = await create_user(db, user, None)
    if not user:
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    user = User(**user.dict())
    return UserInResponse(user=user)
