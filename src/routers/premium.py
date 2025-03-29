from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_session
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from datetime import datetime

from auth.users import current_active_user
from auth.database import User
from models import Link, Query, User as User_db


router = APIRouter(
    prefix="/premium",
    tags=["Premium"]
)


@router.put("/premium")
async def set_premium(status: bool, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):
    if not current_user:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    await session.execute(update(User_db).where(User_db.id == current_user.id).values(is_premium=status))
    await session.commit()

    return {"status": "success"}


@router.get("/expired_stats")
@cache(expire=60)
async def get_expired_link_stats(session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):

    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to get your expired links stats")
    
    status = await session.execute(select(User_db).where(User_db.id == current_user.id))
    status = status.scalars().first()
    if not status.is_premium:
        raise HTTPException(status_code=403, detail="You should be a premium user to get expired links stats")

    query = select(Link).where(Link.expires_at < datetime.now())
    result = await session.execute(query)
    result = result.scalars()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find any expired links"))
    
    data = [{
        "short_url": f"http://localhost/links/{r.short_code}", 
        "original_url": r.original_url,
        "created_at": r.created_at,
        "clicks": r.clicks,
        "last_accessed": r.last_accessed
    } for r in result]

    return {"status": "success", "data": data}


@router.get("/{short_url}/stats")
@cache(expire=60)
async def get_short_url_stats(short_url: str, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):
    
    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to get short url stats")
    
    status = await session.execute(select(User_db).where(User_db.id == current_user.id))
    status = status.scalars().first()
    if not status.is_premium:
        raise HTTPException(status_code=403, detail="You should be a premium user to get links stats")
    
    query = select(Link).where(Link.short_code == short_url)
    result = await session.execute(query)
    result = result.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find this short code"))
    
    data = {
        "original_url": result.original_url,
        "created_at": result.created_at,
        "clicks": result.clicks,
        "last_accessed": result.last_accessed
    }
    return {"status": "success", "data": data}


@router.get("/{short_url}/queries")
@cache(expire=60)
async def get_short_url_queries(short_url: str, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):

    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to get short url queries")
    
    status = await session.execute(select(User_db).where(User_db.id == current_user.id))
    status = status.scalars().first()
    if not status.is_premium:
        raise HTTPException(status_code=403, detail="You should be a premium user to get short url queries")

    query = select(Query).where(Query.short_code == short_url)
    result = await session.execute(query)
    result = result.scalars()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find this short code"))

    data = [{
        "link_id": r.link_id,
        "user_id": r.user_id,
        "short_code": r.short_code,
        "original_link": r.original_link,
        "accessed_at": r.accessed_at
    } for r in result]

    return {"status": "success", "data": data}