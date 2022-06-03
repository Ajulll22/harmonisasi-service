from app.api_models import BaseResponseModel
from app.models.uu import UU
from app.config.db import db_engine
from app.models.preprocessing import Preprocessing
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


class UUResponse(BaseModel):
    id_tbl_uu: int
    presentase: float
    uu: str
    tentang: str
    file_arsip: str
    status: int


class GetUUResponse(BaseResponseModel):
    class Config:
        schema_extra = {
            'example': {
                'value': [
                    {
                        'id_tbl_uu': 10,
                        'presentase': 67.1,
                        'uu': 'UU No 28 Tahun 2009',
                        'tentang': 'PAJAK DAERAH DAN RETRIBUSI DAERAH',
                        'file_arsip': '123123.pdf',
                        'status': 1
                    },
                    {
                        'id_tbl_uu': 20,
                        'presentase': 58.2,
                        'uu': 'UU No 14 Tahun 2019',
                        'tentang': 'Pekerja Sosial',
                        'file_arsip': '123123.pdf',
                        'status': 1
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


async def harmonisasi_file(file: str):
    UU_Title = []
    UU_Content = []

    namaFile = file
    dir = "C:/xampp/htdocs/peraturan-uu/public/assets/hitung/"
    if not os.path.exists(dir + namaFile + ".pdf"):
        raise HTTPException(404, detail='File tidak ditemukan')
    doc = fitz.open(dir + namaFile + ".pdf")
    UU_Title.append(namaFile)
    Content = ""
    for page in doc:
        Content = Content + " " + page.get_text("text")
    UU_Content.append(Content)
    UU_Title_Content = {UU_Title[0]: [UU_Content[0]]}

    UU_Pembanding_df = pd.DataFrame.from_dict(UU_Title_Content).transpose()
    UU_Pembanding_df.columns = ['ISI_UU_Pembanding']
    UU_Pembanding_df = UU_Pembanding_df.sort_index()

    def preptahap1(x): return preproses_tahap1(x)
    UU_Pembanding_Prep = pd.DataFrame(
        UU_Pembanding_df.ISI_UU_Pembanding.apply(preptahap1))
    UU_Pembanding_Prep = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
        lambda x: ' '.join([word for word in x.split() if len(word) > 3])))
    UU_Pembanding_Prep = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
        lambda x: ' '.join([word for word in x.split() if x.count(word) < 5])))
    s_word_indonesia = sw.words('indonesian')
    # print(s_word_indonesia)
    s_word_indonesia.extend(['tanggal', 'diundangkan', 'berlaku', 'ditetapkan', 'lembaran', 'menetapkan',
                            'menteri', 'ayat', 'penetapan', 'dewan', 'berdasarkan', 'persetujuan', 'jakarta', 'huruf', 'rakyat', 'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'])

    UU_Pembanding_Stoprem = pd.DataFrame(UU_Pembanding_Prep.ISI_UU_Pembanding.apply(
        lambda x: ' '.join([word for word in x.split() if word not in (s_word_indonesia)])))

    # list UU Pembanding
    UU_Pembanding_Dokumen = []

    def UU_Pembanding_DF2List(dataset):
        for indeks, line in dataset.iterrows():
            # print(indeks)
            UU_Pembanding_Dokumen.extend(
                [dataset.ISI_UU_Pembanding[indeks].split()])
    UU_Pembanding_DF2List(UU_Pembanding_Stoprem)

    # list UU pasal
    uud_query = Preprocessing.select().join(UU).add_columns(
        UU.c.uu, UU.c.tentang, UU.c.file_arsip, UU.c.status)
    UU_pasal_Stoprem = pd.read_sql_query(uud_query, con=db_engine)

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
            TfIdf_Model[[UU_Query_Dictionary.doc2bow(uu) for uu in dokumen]], matriks_similarity, num_best=1000, normalized=(True, True))
        similarities = indeks[kueri]
        return similarities

    UU_pasal_res = softcossim(
        UU_Pembanding_Dokumen_bigram, UU_pasal_Dokumen_bigram)

    res = []

    for a, x in enumerate(UU_pasal_res):
        pasal = []
        for y in x:
            res_formatter = y[1]*100
            presentase_formatter = float("{:.3f}".format(res_formatter))
            full_dict = {
                'id_tbl_uu': int(UU_pasal_Stoprem.iloc[y[0]].id_tbl_uu),
                'presentase': (presentase_formatter),
                'uu': UU_pasal_Stoprem.iloc[y[0]].uu,
                'tentang': UU_pasal_Stoprem.iloc[y[0]].tentang,
                'file_arsip': UU_pasal_Stoprem.iloc[y[0]].file_arsip,
                'status': int(UU_pasal_Stoprem.iloc[y[0]].status)
            }
            res.append(full_dict)

    return GetUUResponse(
        value=res
    )
