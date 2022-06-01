from sqlalchemy import (
    Column,
    ForeignKey,
    Text,
    Integer,
    String,
    Table
)
from app.config.db import metadata


UU_Pasal = Table(
    'uu_pasal_html',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('id_tbl_uu', Integer, ForeignKey('uu.id_tbl_uu')),
    Column('uud_id', String(255), nullable=True),
    Column('uud_section', String(100), nullable=True),
    Column('uud_content', Text, nullable=True)
)
