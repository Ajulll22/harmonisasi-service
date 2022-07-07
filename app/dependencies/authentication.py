from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from fastapi import Request

import jwt
from typing import Optional

import jwt

from app.config.get_payload import get_payload


class Authentication(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        authorization = await super().__call__(request)

        if not authorization.credentials:
            return {}

        try:
            payload = get_payload(authorization.credentials)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                401,
                detail={
                    'message': 'Token expired',
                    'code': 40100
                }
            )
        except jwt.DecodeError:
            raise HTTPException(
                401,
                detail={
                    'message': 'Token expired',
                    'code': 40101
                }
            )

        return payload
