from app.config.db import db_engine, database
from app.models.preprocessing_pasal import Preprocessing_Pasal

from fastapi import Response

from pydantic import BaseModel
from nltk.corpus import stopwords as sw
import re
import string
import pandas as pd
from typing import List


class TambahRequest(BaseModel):
    id_uu_pasal: int
    uud_content: str


class BulkRequest(BaseModel):
    data: List[TambahRequest]


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


async def tambah_bulk(value: BulkRequest):
    data = value.dict()['data']
    UU_df = pd.DataFrame.from_dict(data)
    UU_df.rename(columns={'uud_content': 'uud_detail'}, inplace=True)

    def preptahap1(x): return preproses_tahap1(x)

    UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(preptahap1))

    UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(lambda x: ' '.join(
        [word for word in x.split() if len(word) > 3])))
    UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(lambda x: ' '.join(
        [word for word in x.split() if x.count(word) < 5])))

    s_word_indonesia = sw.words('indonesian')
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta',
                             'huruf', 'rakyat', 'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli',
                             'agustus', 'september', 'oktober', 'november', 'desember'])

    UU_df.uud_detail = pd.DataFrame(UU_df.uud_detail.apply(lambda x: ' '.join(
        [word for word in x.split() if word not in (s_word_indonesia)])))

    dict = UU_df.to_dict(orient='records')
    # db_engine.execute(Preprocessing_Pasal.insert(), dict)
    query = Preprocessing_Pasal.insert()
    await database.execute_many(query, dict)

    return Response(status_code=201)
