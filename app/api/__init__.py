from fastapi import APIRouter

from app.config.db import database
from app.api.harmonisasi.get_harmonisasi import get_harmonisasi, GetUUResponse

api_router = APIRouter()


@api_router.on_event('startup')
async def startup():
    await database.connect()


@api_router.on_event('shutdown')
async def shutdown():
    await database.disconnect()

api_router.add_api_route('/v1/harmonisasi/{file}', get_harmonisasi,
                         methods=['GET'], tags=['Harmonisasi'], response_model=GetUUResponse)
