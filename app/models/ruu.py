from sqlalchemy import (
    Column,
    Integer,
    String,
    Table
)
from app.config.db import metadata


RUU = Table(
    'ruu',
    metadata,
    Column('id_ruu', Integer, primary_key=True),
    Column('judul_ruu', String(100), nullable=True),
    Column('keyword_ruu', String(100), nullable=True),
    Column('tentang_ruu', String(150), nullable=True),
    Column('file_ruu', String(100), nullable=True)
)
