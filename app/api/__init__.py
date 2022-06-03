from fastapi import APIRouter

from app.config.db import database
from app.api.harmonisasi.harmonisasi_file import harmonisasi_file, GetUUResponse
from app.api.harmonisasi.harmonisasi_pasal import harmonisasi_pasal, HarmonisasiPasalResponse

api_router = APIRouter()


@api_router.on_event('startup')
async def startup():
    await database.connect()


@api_router.on_event('shutdown')
async def shutdown():
    await database.disconnect()

api_router.add_api_route('/v1/harmonisasi/{file}', harmonisasi_file,
                         methods=['GET'], tags=['Harmonisasi'], response_model=GetUUResponse)
api_router.add_api_route('/v1/harmonisasi/pasal', harmonisasi_pasal,
                         methods=['POST'], tags=['Harmonisasi Pasal'], response_model=HarmonisasiPasalResponse)
