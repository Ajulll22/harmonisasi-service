from sqlalchemy import (
    Column,
    ForeignKey,
    Text,
    Integer,
    String,
    Table
)
from app.config.db import metadata


RUU_Pasal = Table(
    'ruu_pasal',
    metadata,
    Column('id_ruu_pasal', Integer, primary_key=True),
    Column('section_ruu', String(50), nullable=True),
    Column('content_ruu', Text, nullable=True),
    Column('id_ruu', Integer, ForeignKey('ruu.id_ruu'))
)
