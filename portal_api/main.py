import os
import asyncpg
import jwt as pyjwt   # 👉 explizit PyJWT
import json           # 👉 fehlt in deinem Code!
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

# === ENV ===
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("API_JWT_SECRET", "portal-secret")

# === APP ===
app = FastAPI(title="Portal API", version="1.0", root_path="/portal")

# CORS fürs Frontend
origins = [
    "http://localhost",
    "http://localhost:8090",  # dein Python-HTTP-Server
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pool: asyncpg.Pool | None = None

# === DB INIT ===
@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS portal_users (
            id SERIAL PRIMARY KEY,
            pers_first_name VARCHAR(100) NOT NULL,
            pers_second_name VARCHAR(100) NOT NULL,
            pers_email VARCHAR(255) UNIQUE,
            pers_tel VARCHAR(50) NOT NULL,
            pers_adress_plz VARCHAR(10) NOT NULL,
            pers_adress_city VARCHAR(100) NOT NULL,
            pers_adress_street VARCHAR(100) NOT NULL,
            pers_adress_building VARCHAR(50) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """)

@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()

# === Auth Helper ===
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Ungültiger Auth-Header")
    token = authorization.split(" ")[1]
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        sub = payload.get("sub")
        if isinstance(sub, str):
            sub = json.loads(sub)   # zurück in dict
        if not isinstance(sub, dict):
            raise ValueError("sub ist nicht gültig")
        return sub
    except Exception as e:
        raise HTTPException(401, f"Ungültiges oder abgelaufenes Token: {e}")

# === Models ===
class PortalUserIn(BaseModel):
    pers_first_name: str
    pers_second_name: str
    pers_email: EmailStr
    pers_tel: str
    pers_adress_plz: str
    pers_adress_city: str
    pers_adress_street: str
    pers_adress_building: str

# === Endpoints ===
@app.post("/users", status_code=201)
async def create_portal_user(data: PortalUserIn, user=Depends(get_current_user)):
    async with pool.acquire() as conn:
        uid = await conn.fetchval("""
            INSERT INTO portal_users (
                pers_first_name, pers_second_name, pers_email, pers_tel,
                pers_adress_plz, pers_adress_city, pers_adress_street, pers_adress_building
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT (pers_email) DO UPDATE SET
                pers_first_name=EXCLUDED.pers_first_name,
                pers_second_name=EXCLUDED.pers_second_name,
                pers_tel=EXCLUDED.pers_tel,
                pers_adress_plz=EXCLUDED.pers_adress_plz,
                pers_adress_city=EXCLUDED.pers_adress_city,
                pers_adress_street=EXCLUDED.pers_adress_street,
                pers_adress_building=EXCLUDED.pers_adress_building
            RETURNING id
        """, data.pers_first_name, data.pers_second_name, data.pers_email,
             data.pers_tel, data.pers_adress_plz, data.pers_adress_city,
             data.pers_adress_street, data.pers_adress_building)
    return {"id": uid, "message": f"Portal-User gespeichert: {data.pers_email}"}

@app.get("/users/me")
async def get_my_portal_user(user=Depends(get_current_user)):
    email = user["email"]
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM portal_users WHERE pers_email=$1", email)
    if not row:
        raise HTTPException(404, "Keine Portal-User-Daten gefunden")
    return dict(row)
