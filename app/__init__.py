from fastapi import FastAPI
import os

from app.config.db import metadata, db_engine
from app.api import api_router


metadata.create_all(db_engine)

app = FastAPI()

app.include_router(api_router)
