import os
import asyncpg
from fastapi import FastAPI

app = FastAPI(title="Business API", version="1.0")

# Dictionary für mehrere Pools
db_pools = {}

@app.on_event("startup")
async def startup():
    global db_pools
    # Liste der Business-DBs aus ENV
    db_names = os.getenv("BUSINESS_DBS", "").split(",")
    for name in db_names:
        url = os.getenv(f"{name.upper()}_URL")  # z.B. BUSINESS_DB1_URL
        if not url:
            raise RuntimeError(f"Keine URL für {name} in ENV gefunden")
        pool = await asyncpg.create_pool(url)
        db_pools[name] = pool
    print(f"Business API: {len(db_pools)} Datenbanken verbunden")

@app.on_event("shutdown")
async def shutdown():
    for pool in db_pools.values():
        await pool.close()

@app.get("/status")
async def status():
    return {"connected_dbs": list(db_pools.keys())}
