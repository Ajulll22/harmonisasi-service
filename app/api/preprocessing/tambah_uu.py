from app.config.db import db_engine, database
from app.models.preprocessing import Preprocessing
from app.api_models import BaseResponseModel

from fastapi import Response

from pydantic import BaseModel
from nltk.corpus import stopwords as sw
import re
import string
import pandas as pd
import fitz


class TambahUURequest(BaseModel):
    id_tbl_uu: int
    file: str


class TambahUUResponse(BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': {
                    'text': 'hasil ekstrak text file pdf'
                },
                'meta': {},
                'message': 'Success',
                'success': True,
                'code': 200
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


async def tambah_uu(data: TambahUURequest):
    dir = "C:/xampp/htdocs/peraturan-uu/public/assets/pdf/"

    doc = fitz.open(dir + data.file)
    Content = ""
    for page in doc:
        Content = Content + " " + page.get_text("text")
    UU_Content = {'Content': [Content]}
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

    content = UU_df.iloc[0].Content

    query = Preprocessing.insert().values(id_tbl_uu=data.id_tbl_uu, content=content)
    await database.execute(query)
    res = []

    hasil = {'text': Content}
    res.append(hasil)

    return TambahUUResponse(
        value=res
    )
