from typing import Optional
from pydantic import BaseModel

class ReleaseRequest(BaseModel):
    repository: str
    release: str
    historical_window: int = 10
