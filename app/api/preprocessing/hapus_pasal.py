from app.config.db import db_engine, database
from app.models.preprocessing_pasal import Preprocessing_Pasal

from fastapi import HTTPException, Response


async def hapus_pasal(id:int):
    check = Preprocessing_Pasal.select(
        Preprocessing_Pasal.c.id_uu_pasal
    ).where(Preprocessing_Pasal.c.id_uu_pasal == id)
    check_id = await database.fetch_one(check)

    if not check_id:
        raise HTTPException(status_code=404, detail='Data tidak ditemukan')

    query = Preprocessing_Pasal.delete().where(Preprocessing_Pasal.c.id_uu_pasal == id)
    await database.execute(query)

    return Response(status_code=204)
