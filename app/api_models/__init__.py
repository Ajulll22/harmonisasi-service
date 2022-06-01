from pydantic import BaseModel
from typing import Any


class BaseResponseModel(BaseModel):
    data: Any = {}
    meta: dict = {}
    success: bool = True
    code: int = 200
    message: str = 'Success'
