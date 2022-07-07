from app.api.draft.keyword_pasal import DraftPasalResponse
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


class DetailResponse(BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': {
                    "kata": "digital elektronik informasi",
                    "hasil": [
                        {
                            "id": 94414,
                            "uud_id": "pasal~5 ayat~3",
                            "uud_content": "Informasi Elektronik dan/atau Dokumen Elektronik \ndinyatakan sah apabila menggunakan Sistem Elektronik \nsesuai dengan ketentuan yang diatur dalam Undang-Undang ini. ",
                            "presentase": 49.622
                        },
                        {
                            "id": 94458,
                            "uud_id": "pasal~22 ayat~1",
                            "uud_content": "Penyelenggara Agen Elektronik tertentu harus menyediakan fitur \npada Agen Elektronik yang dioperasikannya yang \nmemungkinkan penggunanya melakukan perubahan \ninformasi yang masih dalam proses transaksi. ",
                            "presentase": 44.349
                        },
                    ]
                },
                'meta': {},
                'message': 'Success',
                'success': True,
                'code': 200
            }
        }


async def show_detail(id: int):
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

    # list pasal UU
    uu_pasal = UU_Pasal.select().join(UU).join(Preprocessing_Pasal).add_columns(
        Preprocessing_Pasal.c.uud_detail).filter(UU.c.id_tbl_uu == id)
    UU_Stoprem = pd.read_sql_query(uu_pasal, con=db_engine)

    if UU_Stoprem.empty:
        raise HTTPException(404, 'Data tidak ditemukan')

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
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=50, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_Query_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_Dokumen_bigram)
    temp_hasil = {
        'kata': RUU_df.iloc[0].keyword_ruu,
        'hasil': []
    }

    for a, x in enumerate(UU_Query_res):

        for y in x:
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            hasil = {
                'id': int(UU_Stoprem.iloc[y[0]].id),
                'uud_id': UU_Stoprem.iloc[y[0]].uud_id,
                'uud_content': UU_Stoprem.iloc[y[0]].uud_content,
                'presentase': (presentase_formatter)
            }
            temp_hasil['hasil'].append(hasil)

    return DraftPasalResponse(
        value=temp_hasil
    )
