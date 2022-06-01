from sqlalchemy import MetaData, create_engine
from databases import Database

DATABASE_URL = 'mysql://root:@localhost/omnilaw'

db_engine = create_engine(DATABASE_URL)
metadata = MetaData()

database = Database(DATABASE_URL)
