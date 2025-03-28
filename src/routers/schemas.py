from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class LinkCreate(BaseModel):
    original_link: str
    custom_alias: Optional[str] = None
    expires_at: Optional[str] = None