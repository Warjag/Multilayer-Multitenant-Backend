import os
import asyncpg
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Customer API", version="1.0")
pool = None

# ---- Schema ----
class CustomerIn(BaseModel):
    org_name: str
    org_email: EmailStr
    org_tel: str
    org_adress_plz: str
    org_adress_city: str
    org_adress_street: str
    org_adress_building: str

# ---- Startup / Shutdown ----
@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS customer (
            id SERIAL PRIMARY KEY,
            business_db_name VARCHAR(50) NOT NULL DEFAULT 'business_db1',
            org_name VARCHAR(255) NOT NULL,
            org_email VARCHAR(255) UNIQUE,
            org_tel VARCHAR(50) NOT NULL,
            org_adress_plz VARCHAR(10) NOT NULL,
            org_adress_city VARCHAR(100) NOT NULL,
            org_adress_street VARCHAR(100) NOT NULL,
            org_adress_building VARCHAR(50) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """)

@app.on_event("shutdown")
async def shutdown():
    await pool.close()

# ---- Endpoints ----
@app.post("/customer", status_code=201)
async def create_customer(data: CustomerIn):
    async with pool.acquire() as conn:
        cid = await conn.fetchval("""
            INSERT INTO customer (
                org_name, org_email, org_tel,
                org_adress_plz, org_adress_city,
                org_adress_street, org_adress_building
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            RETURNING id
        """, data.org_name, data.org_email, data.org_tel,
             data.org_adress_plz, data.org_adress_city,
             data.org_adress_street, data.org_adress_building)
    return {"message": "Customer erstellt", "customer_id": cid}

@app.get("/customer/{customer_id}")
async def get_customer(customer_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM customer WHERE id=$1", customer_id)
    if not row:
        raise HTTPException(404, "Customer nicht gefunden")
    return dict(row)

