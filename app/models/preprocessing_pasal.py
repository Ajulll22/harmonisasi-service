from sqlalchemy import (
    Column,
    ForeignKey,
    Text,
    Integer,
    String,
    Table
)
from app.config.db import metadata


Preprocessing_Pasal = Table(
    'preprocessing_pasal',
    metadata,
    Column('id_prep_pasal', Integer, primary_key=True),
    Column('id_uu_pasal', Integer, ForeignKey('uu_pasal_html.id')),
    Column('uud_detail', Text)
)
