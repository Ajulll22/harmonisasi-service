from fastapi import APIRouter

from app.config.db import database
from app.api.harmonisasi.harmonisasi_file import harmonisasi_file, GetUUResponse
from app.api.harmonisasi.harmonisasi_keyword import harmonisasi_keyword, HarmonisasiKeywordResponse
from app.api.harmonisasi.show_detail import show_detail, DetailResponse

from app.api.preprocessing.tambah_bulk import tambah_bulk
from app.api.preprocessing.tambah_uu import tambah_uu, TambahUUResponse

from app.api.draft.keyword_pasal import keyword_pasal, DraftPasalResponse

api_router = APIRouter()


@api_router.on_event('startup')
async def startup():
    await database.connect()


@api_router.on_event('shutdown')
async def shutdown():
    await database.disconnect()

api_router.add_api_route('/v1/harmonisasi/file/{file}', harmonisasi_file,
                         methods=['GET'], tags=['Harmonisasi'], response_model=GetUUResponse, description='Harmonisasi RUU ekstensi file pdf dengan UU yang telah ada di dalam database')
api_router.add_api_route('/v1/harmonisasi/keyword', harmonisasi_keyword,
                         methods=['GET'], tags=['Harmonisasi'], response_model=HarmonisasiKeywordResponse, description='Harmonisasi berdasarkan keyword pada RUU')
api_router.add_api_route('/v1/harmonisasi/detail/{id}', show_detail,
                         methods=['GET'], tags=['Harmonisasi'], response_model=DetailResponse, description='Melihat letak kesamaan pada UU dan RUU')

api_router.add_api_route('/v1/preprocessing_bulk', tambah_bulk,
                         methods=['POST'], tags=['Preprocessing'], status_code=201, description='Preprocessing pasal dengan request dict')
api_router.add_api_route('/v1/preprocessing_uu', tambah_uu,
                         methods=['POST'], tags=['Preprocessing'], status_code=201, description='Preprocessing UU dan mengembalikan hasil ekstraksi text full')

api_router.add_api_route('/v1/draft/pasal', keyword_pasal,
                         methods=['POST'], tags=['Draft'], response_model=DraftPasalResponse, description='Drafting dengan teknik harmonisasi menggunakan search key')
