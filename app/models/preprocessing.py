from sqlalchemy import (
    Column,
    ForeignKey,
    Text,
    Integer,
    String,
    Table
)
from app.config.db import metadata


Preprocessing = Table(
    'preprocessing',
    metadata,
    Column('id_preprocessing', Integer, primary_key=True),
    Column('id_tbl_uu', Integer, ForeignKey('uu.id_tbl_uu')),
    Column('content', Text)
)
