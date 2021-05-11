from datetime import timedelta, datetime

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient

from api.db import get_database
from api.services import create_user, get_user
from api.schemas import Token, UserInCreate, User, UserInResponse
from api.config import SIGN_ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"])
router = APIRouter(tags=["auth"],)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(db, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=SIGN_ALGORITHM)
    return encoded_jwt


@router.post(
    "/user/register",
    response_model=UserInResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserInCreate, db: AsyncIOMotorClient = Depends(get_database)
):
    hashed_password = get_password_hash(user.password)
    user = await create_user(db, user, hashed_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )
    user = User(**user.dict())
    access_token = create_access_token({"sub": user.username})
    token = Token(access_token=access_token, token_type="bearer")
    return UserInResponse(user=user, token=token)


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncIOMotorClient = Depends(get_database),
):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = form_data.username
    password = form_data.password
    if not await authenticate_user(db, username, password):
        raise exception
    access_token = create_access_token({"sub": username})
    token = Token(access_token=access_token, token_type="bearer")
    return token
