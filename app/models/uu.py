from sqlalchemy import (
    Column,
    ForeignKey,
    Text,
    Integer,
    String,
    Table
)
from app.config.db import metadata


UU = Table(
    'uu',
    metadata,
    Column('id_tbl_uu', Integer, primary_key=True),
    Column('uu', String(1000), nullable=True),
    Column('tentang', String(1000), nullable=True),
    Column('file_arsip', String(255)),
    Column('status', Integer),
    Column('id_kategori', Integer)
)
