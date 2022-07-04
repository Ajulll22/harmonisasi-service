from app.config.db import db_engine, database
from app.models.preprocessing_pasal import Preprocessing_Pasal
from app.api_models import BaseResponseModel

from fastapi import Response

from pydantic import BaseModel
from nltk.corpus import stopwords as sw
import re
import string
import pandas as pd

class UbahPasalRequest(BaseModel):
    id_uu_pasal: int
    uud_content: str

class UbahPasalResponse(BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': {},
                'meta': {},
                'message': 'Success',
                'success': True,
                'code': 204
            }
        }

def preproses_tahap1(text):
    text = text.lower()
    text = re.sub('www.peraturan.go.id', '', text)
    text = re.sub('www.bphn.go.id', '', text)
    text = re.sub('www.hukumonline.com', '', text)
    # untuk menghilangkan teks yang berada di dalam []
    text = re.sub('\[.*?\]', '', text)
    # untuk menghilangkan karakter non ascii
    text = text.encode('ascii', 'replace').decode('ascii')
    # Untuk menghilangkan punktuasi (tanda baca) yang berada di dalam teks
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text)
    # untuk menghilangkan kata yang terdapat angka di dalammnya
    text = re.sub('\w*\d\w*', '', text)
    text = re.sub('[‘’“”…]', '', text)
    text = re.sub('\n', ' ', text)
    text = re.sub('\t', ' ', text)
    text = text.strip()
    text = re.sub('microsoft word', '', text)
    text = re.sub('�', '', text)
    text = re.sub('\s+', ' ', text)
    # untuk menghilangkan single char
    text = re.sub(r"\b[a-zA-Z]\b", "", text)
    text = re.sub('www.bphn.go.id', '', text)
    text = re.sub('copyright', '', text)
    text = re.sub('menirr', '', text)
    text = re.sub('nomor', '', text)
    text = re.sub('repuel', '', text)
    text = re.sub('indonesta', 'indonesia', text)
    text = re.sub('rtf', '', text)
    text = re.sub('republtk', 'republik', text)
    return text

async def ubah_pasal(data: UbahPasalRequest):
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
    
    query = Preprocessing_Pasal.update().where(Preprocessing_Pasal.c.id_uu_pasal == data.id_uu_pasal
                                   ).values(uud_detail=uud_detail_new)
    await database.execute(query)

    return Response(status_code=204)
