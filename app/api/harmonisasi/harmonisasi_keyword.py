from app.api_models import BaseResponseModel
from app.models.uu import UU
from app.models.uu_pasal import UU_Pasal
from app.models.ruu import RUU
from app.models.ruu_pasal import RUU_Pasal
from app.config.db import db_engine
from app.models.preprocessing import Preprocessing
from app.models.preprocessing_pasal import Preprocessing_Pasal
from app.dependencies import basedir

from fastapi.exceptions import HTTPException

from nltk.corpus import stopwords as sw
import pandas as pd
from gensim.models.phrases import Phrases, Phraser
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from gensim.similarities import SparseTermSimilarityMatrix
from gensim.similarities import SoftCosineSimilarity


class HarmonisasiKeywordResponse (BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': [
                    {
                        'id_tbl_uu': 192,
                        'uu': 'UU No 11 Tahun 2008',
                        'presentase': 56.21,
                        'tentang': 'INFORMASI DAN TRANSAKSI ELEKTRONIK',
                        'file_arsip': '2008-11.pdf',
                        'status': 3,
                        'id_kategori': 8,
                    },
                    {
                        'id_tbl_uu': 193,
                        'uu': 'UU No 8 Tahun 2017',
                        'presentase': 48.79,
                        'tentang': 'Perubahan Atas Undang-Undang Nomor 18 Tahun 2016 Tentang Anggaran Pendapatan Dan Belanja Negara Tahun Anggaran 2017',
                        'file_arsip': '123123.pdf',
                        'status': 3,
                        'id_kategori': 3,
                    },
                ],
                'meta': {},
                'message': 'Success',
                'success': True,
                'code': 200
            }
        }


async def harmonisasi_keyword():
    row = RUU.select().order_by(RUU.c.id_ruu.desc())
    full = pd.read_sql_query(row, con=db_engine)
    RUU_df = full.head(1)

    # list UU Pembanding
    UU_Pembanding_Dokumen = []

    def UU_Pembanding_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Pembanding_Dokumen.extend(
                [dataset.keyword_ruu[indeks].split()])

    UU_Pembanding_DF2List(RUU_df)

    # list UU Pasal
    uu_query = Preprocessing.select().join(UU).add_columns(
        UU.c.uu, UU.c.tentang, UU.c.file_arsip, UU.c.status, UU.c.id_kategori)
    UU_pasal_Stoprem = pd.read_sql_query(uu_query, con=db_engine)

    UU_pasal_Dokumen = []

    def UU_pasal_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_pasal_Dokumen.extend([dataset.content[indeks].split()])

    UU_pasal_DF2List(UU_pasal_Stoprem)

    # Membuat bigram untuk UU_Pembanding_Dokumen
    UU_Pembanding_Dokumen_phrases = Phrases(
        UU_Pembanding_Dokumen, min_count=10, progress_per=1)
    bigram_Pembanding = Phraser(UU_Pembanding_Dokumen_phrases)
    UU_Pembanding_Dokumen_bigram = bigram_Pembanding[UU_Pembanding_Dokumen]

    # Membuat bigram untuk UU_pasal_Dokumen
    UU_pasal_Dokumen_phrases = Phrases(
        UU_pasal_Dokumen, min_count=10, progress_per=1)
    bigram_pasal = Phraser(UU_pasal_Dokumen_phrases)
    UU_pasal_Dokumen_bigram = bigram_pasal[UU_pasal_Dokumen]

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
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=2000, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_pasal_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_pasal_Dokumen_bigram)

    res = []

    for a, x in enumerate(UU_pasal_res):
        for y in x:
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            full_dict = {
                'id_tbl_uu': int(UU_pasal_Stoprem.iloc[y[0]].id_tbl_uu),
                'presentase': (presentase_formatter),
                'uu': UU_pasal_Stoprem.iloc[y[0]].uu,
                'tentang': UU_pasal_Stoprem.iloc[y[0]].tentang,
                'file_arsip': UU_pasal_Stoprem.iloc[y[0]].file_arsip,
                'status': int(UU_pasal_Stoprem.iloc[y[0]].status),
                'id_kategori': int(UU_pasal_Stoprem.iloc[y[0]].id_kategori)
            }
            res.append(full_dict)

    return HarmonisasiKeywordResponse(
        value=res
    )
