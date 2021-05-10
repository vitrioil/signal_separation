from typing import Optional
from pydantic import BaseModel

from api.schemas import Token


class User(BaseModel):
    username: str
    email: Optional[str] = None


class UserInDB(User):
    hashed_password: str


class UserInCreate(User):
    password: str


class UserInResponse(BaseModel):
    user: User
    token: Optional[Token] = None
