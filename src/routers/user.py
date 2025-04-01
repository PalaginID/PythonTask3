from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from typing import Optional
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re
import secrets

from database import get_async_session
from auth.users import current_active_user
from auth.database import User
from routers.schemas import LinkCreate
from models import Link, Query


days_before_expire = 1

router = APIRouter(
    prefix="/links",
    tags=["Links"]
)


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False

  
def is_valid_short_code(short_code: str) -> bool:
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.fullmatch(pattern, short_code))


def is_valid_date_format(date_string: str) -> bool:
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            datetime.strptime(date_string, fmt)
            return True
        except ValueError:
            continue
    return False


@router.post("/shorten")
async def shorten_link(request: LinkCreate, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):

    if not is_valid_url(request.original_link):
        raise HTTPException(status_code=400, detail="Invalid URL")
    

    if request.custom_alias:
        if not is_valid_short_code(request.custom_alias):
            raise HTTPException(status_code=400, detail="Invalid custom alias")
        query = select(Link).where(Link.short_code == request.custom_alias)
        result = await session.execute(query)
        if result.scalars().all():
            raise HTTPException(status_code=400, detail="Custom alias already exists")
        short_code = request.custom_alias
    else:
        while True:
            short_code = secrets.token_urlsafe(6)
            query = select(Link).where(Link.short_code == short_code)
            result = await session.execute(query)
            if not result.scalars().all():
                break

    create_date = datetime.now()
    create_date = datetime.fromisoformat(create_date.strftime("%Y-%m-%d %H:%M"))

    if request.expires_at:
        try:
            expires_date = datetime.fromisoformat(request.expires_at)
        except Exception as e:
            raise HTTPException(status_code=400, detail=("Cannot format expires_at to date")) from e
    else:
        expires_date = create_date + timedelta(days=days_before_expire)
    
    user_id = current_user.id if current_user else None

    link_data = {
        "short_code": short_code,
        "original_url": request.original_link,
        "created_at": create_date,
        "expires_at": expires_date,
        "clicks": 0,
        "last_accessed": None,
        "owner_id": user_id
    }
    
    query = insert(Link).values(**link_data)
    try:
        await session.execute(query)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Something went wrong. Try again later") from e
    return {"status": "success", "short_url": f"http://localhost/links/{short_code}"}


@router.get("/search")
@cache(expire=60)
async def search_short_url(original_url: str, session: AsyncSession = Depends(get_async_session)):
    query = select(Link).where(Link.original_url == original_url)
    result = await session.execute(query)
    result = result.scalars().all()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find this original url"))
    
    data = [{"short_url": f"http://localhost/links/{r.short_code}"} for r in result]

    return {"status": "success", "data": data}


@router.get("/expired_stats")
@cache(expire=60)
async def get_expired_link_stats(session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):

    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to get your expired links stats")

    query = select(Link).where(Link.expires_at < datetime.now()).filter(Link.owner_id == current_user.id)
    result = await session.execute(query)
    result = result.scalars().all()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find expired links created by you"))
    
    data = [{
        "short_url": f"http://localhost/links/{r.short_code}", 
        "original_url": r.original_url,
        "created_at": r.created_at,
        "clicks": r.clicks,
        "last_accessed": r.last_accessed,
        "expires_at": r.expires_at
    } for r in result]

    return {"status": "success", "data": data}



@router.get("/{short_url}")
@cache(expire=60)
async def url_redirect(short_url: str, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):
    query = select(Link).where(Link.short_code == short_url)
    message = await session.execute(query)
    result = message.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find this short code"))
    if result.expires_at < datetime.fromisoformat(datetime.now().strftime("%Y-%m-%d %H:%M")):
        raise HTTPException(status_code=410, detail=("Short link has expired"))
    
    access_time = datetime.now()
    access_time = datetime.fromisoformat(access_time.strftime("%Y-%m-%d %H:%M"))

    try:
        query = insert(Query).values(
            link_id=result.id,
            user_id=current_user.id if current_user else None,
            short_code=short_url,
            original_link=result.original_url,
            accessed_at=access_time
            )
        await session.execute(query)
        
        result.last_accessed = access_time
        result.clicks += 1
        result.expires_at = access_time + timedelta(days=days_before_expire)
        await session.commit()
        return RedirectResponse(url=result.original_url)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Something went wrong. Try again later") from e


@router.get("/{short_url}/stats")
@cache(expire=60)
async def get_short_url_stats(short_url: str, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):
    
    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to get short url stats")
    
    query = select(Link).where(Link.short_code == short_url)
    result = await session.execute(query)
    result = result.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find this short code"))
    if result.owner_id and not result.owner_id == current_user.id:
        raise HTTPException(status_code=403, detail=("Cannot get stats for short codes created by other logged in users"))
    print(result.expires_at)
    if datetime.fromisoformat(result.expires_at.strftime("%Y-%m-%d %H:%M")) < datetime.fromisoformat(datetime.now().strftime("%Y-%m-%d %H:%M")):
        raise HTTPException(status_code=404, detail=("Short link has expired. Use /expired_stats instead."))
    
    data = {
        "original_url": result.original_url,
        "created_at": result.created_at,
        "clicks": result.clicks,
        "last_accessed": result.last_accessed,
        "expires_at": result.expires_at
    }
    return {"status": "success", "data": data}


@router.put("/{short_url}")
async def update_short_url(short_url: str, new_alias: Optional[str], session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)):
    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to update short urls")
    
    if new_alias and not is_valid_short_code(new_alias):
        raise HTTPException(status_code=400, detail=("Invalid new alias"))
    
    query = select(Link).where(Link.short_code == short_url)
    result = await session.execute(query)
    result_link = result.scalars().first()

    if not result_link:
        raise HTTPException(status_code=404, detail=("Cannot find this short code"))
    elif result_link.owner_id and not result_link.owner_id == current_user.id:
        raise HTTPException(status_code=403, detail=("Cannot update short codes created by other logged in users"))
    
    if not new_alias or new_alias is None:
        while True:
            new_alias = secrets.token_urlsafe(6)
            query = select(Link).where(Link.short_code == new_alias)
            result = await session.execute(query)
            if not result.scalars().all():
                break
    else:
        query = select(Link).where(Link.short_code == new_alias)
        result = await session.execute(query)
        if result.scalars().all():
            raise HTTPException(status_code=400, detail=("Short code already exists"))
    
    create_time = datetime.now()
    create_time = datetime.fromisoformat(create_time.strftime("%Y-%m-%d %H:%M"))

    data_link = {
        "short_code": new_alias,
        "created_at": create_time
    }

    data_query ={
        "short_code": new_alias
    }

    try:
        query = update(Link).where(Link.id == result_link.id).values(**data_link)
        await session.execute(query)
        await session.commit()

        query = update(Query).where(Query.link_id == result_link.id).values(**data_query)
        await session.execute(query)
        await session.commit()
        return {"status": "success", "message": "Short url updated", "short_url": f"http://localhost/links/{new_alias}"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Something went wrong. Try again later") from e


@router.delete("/{short_url}")
async def delete_short_url(short_url: str, session: AsyncSession = Depends(get_async_session), current_user: Optional[User] = Depends(current_active_user)): 
    if not current_user:
        raise HTTPException(status_code=403, detail="You should log in to delete short urls")
    
    query = select(Link).where(Link.short_code == short_url)
    result = await session.execute(query)
    result = result.scalars().first()

    if not result:
        raise HTTPException(status_code=404, detail=("Cannot find this short code"))
    elif result.owner_id and not result.owner_id == current_user.id:
        raise HTTPException(status_code=403, detail=("Cannot delete short codes created by other logged in users"))
    
    try:
        query = delete(Link).where(Link.short_code == short_url)
        await session.execute(query)
        await session.commit()
        return {"status": "success", "message": "Short url deleted"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Something went wrong. Try again later") from e