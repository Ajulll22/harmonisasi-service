from sqlalchemy import MetaData, create_engine
from databases import Database

from app.config import config


db_engine = create_engine(config.DB)
metadata = MetaData()

database = Database(config.DB)
