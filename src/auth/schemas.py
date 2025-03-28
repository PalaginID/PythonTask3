import uuid

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    email: str


class UserCreate(schemas.BaseUserCreate):
    email: str
    password: str