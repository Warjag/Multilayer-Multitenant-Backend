import os
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="Admin API", version="1.0")
pool = None

class AdminIn(BaseModel):
    email: EmailStr
    role: str

@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """)

@app.on_event("shutdown")
async def shutdown():
    await pool.close()

@app.post("/admin", status_code=201)
async def create_admin(data: AdminIn):
    async with pool.acquire() as conn:
        aid = await conn.fetchval(
            "INSERT INTO admins (email, role) VALUES ($1,$2) RETURNING id",
            data.email, data.role
        )
    return {"admin_id": aid, "email": data.email, "role": data.role}

@app.get("/admin/{aid}")
async def get_admin(aid: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM admins WHERE id=$1", aid)
    if not row:
        raise HTTPException(404, "Admin nicht gefunden")
    return dict(row)
