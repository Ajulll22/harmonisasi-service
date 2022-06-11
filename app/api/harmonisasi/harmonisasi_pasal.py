from app.api_models import BaseResponseModel
from app.models.uu import UU
from app.models.uu_pasal import UU_Pasal
from app.config.db import db_engine
from app.models.preprocessing import Preprocessing
from app.models.preprocessing_pasal import Preprocessing_Pasal
from app.dependencies import basedir

from fastapi.exceptions import HTTPException

from pydantic import BaseModel
from nltk.corpus import stopwords as sw
import fitz
import re
import string
import os
import pandas as pd
from gensim.models.phrases import Phrases, Phraser
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.similarities import SparseTermSimilarityMatrix
from gensim.similarities import SoftCosineSimilarity
import os
from itertools import groupby


class PasalRequest(BaseModel):
    kalimat: str


class HarmonisasiPasalResponse(BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': [
                    {
                        'id_tbl_uu': 192,
                        'uu': 'UU No 8 Tahun 2017',
                        'jumlah': 1,
                        'tentang': 'Perubahan Atas Undang-Undang Nomor 18 Tahun 2016 Tentang Anggaran Pendapatan Dan Belanja Negara Tahun Anggaran 2017',
                        'file_arsip': '123123.pdf',
                        'status': 1,
                        'id_kategori': 3,
                        'pasal': [
                            {
                                'presentase': 45.3,

                            }
                        ]
                    },
                ],
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


async def harmonisasi_pasal(data: PasalRequest):
    UU_Content = {'Content': [data.kalimat]}
    UU_df = pd.DataFrame.from_dict(UU_Content)

    UU_df = pd.DataFrame.from_dict(UU_Content)

    def preptahap1(x): return preproses_tahap1(x)

    UU_df = pd.DataFrame(UU_df.Content.apply(preptahap1))

    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if len(word) > 3])))
    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if x.count(word) < 5])))

    s_word_indonesia = sw.words('indonesian')
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat', 'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

    UU_df = pd.DataFrame(UU_df.Content.apply(lambda x: ' '.join(
        [word for word in x.split() if word not in (s_word_indonesia)])))

    # list UU Pembanding
    UU_Pembanding_Dokumen = []

    def UU_Pembanding_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Pembanding_Dokumen.extend(
                [dataset.Content[indeks].split()])
    UU_Pembanding_DF2List(UU_df)

    # list UU pasal
    uu_pasal = UU_Pasal.select().join(UU).join(Preprocessing_Pasal).add_columns(
        UU.c.uu, UU.c.tentang, UU.c.id_kategori, UU.c.status, UU.c.file_arsip, Preprocessing_Pasal.c.uud_detail)
    UU_Stoprem = pd.read_sql_query(uu_pasal, con=db_engine)

    UU_Dokumen = []

    def UU_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Dokumen.extend([dataset.uud_detail[indeks].split()])
    UU_DF2List(UU_Stoprem)

    # Membuat bigram untuk UU_Pembanding_Dokumen
    UU_Pembanding_Dokumen_phrases = Phrases(
        UU_Pembanding_Dokumen, min_count=10, progress_per=1)
    bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
    UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

    # Membuat bigram untuk UU_Dokumen
    UU_Dokumen_phrases = Phrases(
        UU_Dokumen, min_count=10, progress_per=1)
    bigram_pasal = Phraser(UU_Dokumen_phrases)
    UU_Dokumen_bigram = bigram_pasal[UU_Dokumen]

    UU_Query_Dictionary = Dictionary.load(
        basedir + '/new_dictionary.gensimdict')

    TfIdf_Model = TfidfModel.load(basedir + '/new_tfidf.model')

    matriks_similarity = SparseTermSimilarityMatrix.load(
        basedir + '/new_matriks.matrix')

    def softcossim(kueri, dokumen):
        # Compute Soft Cosine Measure between the query and the documents.
        kueri = TfIdf_Model[[UU_Query_Dictionary.doc2bow(
            querry) for querry in kueri]]
        indeks = SoftCosineSimilarity(
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=100, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_Query_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)

    for a, x in enumerate(UU_Query_res):
        array = []
        for y in x:

            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))

            tmp_dict = {
                'id': int(UU_Stoprem.iloc[y[0]].id),
                'presentase': (presentase_formatter),
                'id_tbl_uu': int(UU_Stoprem.iloc[y[0]].id_tbl_uu),
                'uu': UU_Stoprem.iloc[y[0]].uu,
                'tentang': UU_Stoprem.iloc[y[0]].tentang,
                'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                'file_arsip': UU_Stoprem.iloc[y[0]].file_arsip,
                'status': int(UU_Stoprem.iloc[y[0]].status),
                'id_kategori': int(UU_Stoprem.iloc[y[0]].id_kategori)
            }
            array.append(tmp_dict)

    res = []
    def key_func(k): return k['id_tbl_uu']

    for k, g in groupby(sorted(array, key=key_func), key=key_func):
        obj = {'id_tbl_uu': k, 'uu': '',
               'jumlah': 0, 'tentang': '', 'file_arsip': '', 'status': '', 'id_kategori': '', 'pasal': []}
        for group in g:
            if not obj['uu']:
                obj['uu'] = group['uu']
                obj['tentang'] = group['tentang']
                obj['file_arsip'] = group['file_arsip']
                obj['status'] = group['status']
                obj['id_kategori'] = group['id_kategori']
            obj['jumlah'] = obj['jumlah'] + 1
            pasal = {
                'id': group['id'],
                'presentase': group['presentase'],
                'uud_id': group['uud_id'],
                'uud_content': group['uud_content']
            }
            obj['pasal'].append(pasal)
        res.append(obj)

    hasil = sorted(res, key=lambda res: res['jumlah'], reverse=True)

    return HarmonisasiPasalResponse(
        value=hasil
    )
