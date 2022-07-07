from app.config.db import db_engine, database
from app.models.preprocessing import Preprocessing
from app.api_models import BaseResponseModel
from app.dependencies.cleaning import preproses_tahap1

from fastapi import HTTPException, Response

from pydantic import BaseModel
from nltk.corpus import stopwords as sw
import pandas as pd


class UbahUURequest(BaseModel):
    content: str

class UbahUUResponse(BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': {
                    'id_tbl_uu': 99
                },
                'meta': {},
                'message': 'Success',
                'success': True,
                'code': 201
            }
        }

async def ubah_uu(id: int, data:UbahUURequest):
    check_id_query = Preprocessing.select(
        Preprocessing.c.id_tbl_uu
    ).where(Preprocessing.c.id_tbl_uu == id)
    check_id = await database.fetch_one(check_id_query)

    if not check_id:
        raise HTTPException(404, detail='Data tidak ditemukan')

    UU_Content = {'Content': [data.content]}

    UU_df = pd.DataFrame.from_dict(UU_Content)

    def preptahap1(x): return preproses_tahap1(x)

    UU_df = pd.DataFrame(UU_df.Content.apply(preptahap1))

    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if len(word) > 3])))
    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if x.count(word) < 5])))

    s_word_indonesia = sw.words('indonesian')
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat'])
    s_word_indonesia.extend(['januari', 'februari', 'maret', 'april', 'mei',
                            'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if word not in (s_word_indonesia)])))

    content_new = UU_df.iloc[0].Content
    query = Preprocessing.update().where(Preprocessing.c.id_tbl_uu == id).values(
        content=content_new
    )
    await database.execute(query)

    return UbahUUResponse(
        value={
            'id_tbl_uu': id
        }
    )
