from app.config.db import db_engine, database
from app.models.preprocessing_pasal import Preprocessing_Pasal
from app.dependencies.cleaning import preproses_tahap1

from fastapi import Response

from pydantic import BaseModel
from nltk.corpus import stopwords as sw
import pandas as pd


class TambahPasalRequest(BaseModel):
    id_uu_pasal: int
    uud_content: str

async def tambah_pasal(data: TambahPasalRequest):
    UU_Content = {'Content': [data.uud_content]}

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

    uud_detail_new = UU_df.iloc[0].Content

    query = Preprocessing_Pasal.insert().values(id_uu_pasal=data.id_uu_pasal, uud_detail=uud_detail_new)

    await database.execute(query)

    return Response(status_code=201)
