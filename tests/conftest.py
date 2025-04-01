import os
import stat
import pytest_asyncio
import asyncio
from fastapi_cache import FastAPICache
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from types import SimpleNamespace
import uuid
import random
from sqlalchemy import delete
from httpx import AsyncClient, ASGITransport

from src.models import User, Link, Query, Base
from src.database import get_async_session
from src.main import app
from src.auth.users import current_active_user

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

test_engine = create_async_engine(os.environ["DATABASE_URL"], echo=True, future=True)
TestAsyncSessionMaker = async_sessionmaker(test_engine, expire_on_commit=False)


# Creating DB schema for future fixture
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_db_schema():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()

    db_path = './test_temp.db'

    try:
        if os.path.exists(db_path):
            os.chmod(db_path, stat.S_IWRITE)
            os.remove(db_path)
    except Exception as e:
        print(f"{e}")


# Overriding dependencies
@pytest_asyncio.fixture(scope="session", autouse=True)
async def override_db_dependency():
    async def _get_test_session():
        async with TestAsyncSessionMaker() as session:
            yield session

    app.dependency_overrides[get_async_session] = _get_test_session
    yield
    app.dependency_overrides.clear()


# Cache fixture
class InMemoryBackend:
    def __init__(self):
        self.store = {}

    async def get(self, key, default=None):
        return self.store.get(key, default)

    async def set(self, key, value, expire=None):
        self.store[key] = value

    async def delete(self, key):
        self.store.pop(key, None)

    async def clear(self, namespace=None, key=None):
        self.store.clear()

    async def get_with_ttl(self, key):
        return None, self.store.get(key)


@pytest_asyncio.fixture(scope="session", autouse=True)
def override_cache():
    in_memory_backend = InMemoryBackend()
    FastAPICache.init(in_memory_backend, prefix="fastapi-cache-test")


transport = None


@pytest_asyncio.fixture(scope="session")
async def test_app():
    global transport
    transport = ASGITransport(app=app)
    return app


@pytest_asyncio.fixture
async def db_session():
    async with TestAsyncSessionMaker() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db(db_session):
    yield
    await db_session.execute(delete(User))
    await db_session.execute(delete(Query))
    await db_session.execute(delete(Link))
    await db_session.commit()


@pytest_asyncio.fixture
def standard_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=f"test{random.randint(10000, 99999)}@example.com",
        hashed_password="notapassword",
        is_active=True,
        is_superuser=False,
        is_premium=False
    )


@pytest_asyncio.fixture
async def standard_client(standard_user, test_app):
    async with TestAsyncSessionMaker() as session:
        session.add(User(
            id=standard_user.id,
            email=standard_user.email,
            hashed_password=standard_user.hashed_password,
            is_active=standard_user.is_active,
            is_superuser=standard_user.is_superuser,
            is_premium=standard_user.is_premium
        ))
        await session.commit()
    async def override_get_current_user():
        return standard_user

    test_app.dependency_overrides[current_active_user] = override_get_current_user

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    test_app.dependency_overrides.pop(current_active_user, None)


@pytest_asyncio.fixture
def premium_user():
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=f"test{random.randint(10000, 99999)}@example.com",
        hashed_password="notapassword",
        is_active=True,
        is_superuser=False,
        is_premium=True
    )


@pytest_asyncio.fixture
async def premium_client(premium_user, test_app):
    async with TestAsyncSessionMaker() as session:
        session.add(User(
            id=premium_user.id,
            email=premium_user.email,
            hashed_password=premium_user.hashed_password,
            is_active=premium_user.is_active,
            is_superuser=premium_user.is_superuser,
            is_premium=True
        ))
        await session.commit()
    async def override_get_current_user():
        return premium_user

    test_app.dependency_overrides[current_active_user] = override_get_current_user

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    test_app.dependency_overrides.pop(current_active_user, None)


@pytest_asyncio.fixture
async def anon_client(test_app):
    test_app.dependency_overrides.pop(current_active_user, None)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()