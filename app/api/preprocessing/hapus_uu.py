from app.config.db import db_engine, database
from app.models.preprocessing import Preprocessing

from fastapi import HTTPException, Response


async def hapus_uu(id: int):
    check = Preprocessing.select(
        Preprocessing.c.id_tbl_uu
    ).where(Preprocessing.c.id_tbl_uu == id)
    check_id = await database.fetch_one(check)

    if not check_id:
        raise HTTPException(status_code=404, detail='Data Tidak Ditemukan')

    query = Preprocessing.delete().where(Preprocessing.c.id_tbl_uu == id)

    await database.execute(query)

    return Response(status_code=204)