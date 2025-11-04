import os
import jwt as pyjwt    # 👉 explizit PyJWT
import json
import asyncpg
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from argon2 import PasswordHasher
from datetime import datetime, timedelta, timezone

# === ENV ===
DATABASE_URL = os.getenv("AUTH_DATABASE_URL")
JWT_SECRET = os.getenv("API_JWT_SECRET", "super_secret_shared_key")
ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("API_ACCESS_TOKEN_EXPIRE_MIN", "60"))
PORTAL_API_URL = os.getenv("PORTAL_API_URL", "http://portal_api:8000/portal")

# --- Mailserver ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("GMAIL_USER")
SMTP_PASS = os.getenv("GMAIL_APP_PASS")

# === APP ===
app = FastAPI(title="Auth API", version="1.0", root_path="/auth")

# === CORS fürs Frontend ===
origins = [
    "http://localhost",
    "http://localhost:8090",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ph = PasswordHasher()
pool: asyncpg.Pool | None = None


# === Models ===
class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# === JWT Helper ===
def create_token(sub: dict):
    """
    sub wird als JSON-String gespeichert, damit Portal-API
    beim Dekodieren mit json.loads() wieder ein dict bekommt.
    """
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    return pyjwt.encode(
        {"sub": json.dumps(sub), "exp": exp},
        JWT_SECRET,
        algorithm="HS256"
    )

# === Registrations-Email
def send_registration_email(to_email: str):
    """Sendet eine Bestätigungsmail nach erfolgreicher Registrierung."""
    subject = "Willkommen im Portal!"
    body = f"""Hallo {to_email},

danke für deine Registrierung im Portal.
Dein Account wurde erfolgreich erstellt!

Viele Grüße
Dein Portal-Team
"""

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        print(f"📤 Sende E-Mail an {to_email} über {SMTP_SERVER}:{SMTP_PORT} ...")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)

        print(f"✅ Bestätigungsmail an {to_email} gesendet")

    except Exception as e:
        print(f"❌ Fehler beim Senden der Mail an {to_email}: {e}")




# === DB Setup ===
@app.on_event("startup")
async def startup():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            pw_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """)


@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()


# === Endpoints ===
@app.post("/register")
async def register(data: RegisterIn):
    if len(data.password) < 8:
        raise HTTPException(400, "Passwort zu kurz")

    hashed = ph.hash(data.password)

    try:
        async with pool.acquire() as conn:
            user_id = await conn.fetchval(
                "INSERT INTO users (email, pw_hash) VALUES ($1,$2) RETURNING id",
                data.email, hashed
            )

        # ⬇️ Automatisch Portal-User anlegen
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{PORTAL_API_URL}/users",
                headers={"Authorization": f"Bearer {create_token({'user_id': user_id, 'email': data.email})}"},
                json={
                    "pers_first_name": "Vorname",
                    "pers_second_name": "Nachname",
                    "pers_email": data.email,
                    "pers_tel": "0000",
                    "pers_adress_plz": "00000",
                    "pers_adress_city": "City",
                    "pers_adress_street": "Street",
                    "pers_adress_building": "0"
                }
            )
            if resp.status_code >= 400:
                raise HTTPException(500, f"Portal-User konnte nicht angelegt werden: {resp.text}")

        # ⬇️ Bestätigungsmail senden
        send_registration_email(data.email)

        return {"message": "User + Portal-User erstellt, Mail gesendet", "user_id": user_id}

    except asyncpg.UniqueViolationError:
        raise HTTPException(409, "E-Mail bereits registriert")
    except Exception as e:
        raise HTTPException(400, f"Fehler: {e}")


@app.post("/login")
async def login(data: LoginIn):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, email, pw_hash FROM users WHERE email=$1", data.email)
    if not row:
        raise HTTPException(401, "Falsche Zugangsdaten")

    try:
        ph.verify(row["pw_hash"], data.password)
    except Exception:
        raise HTTPException(401, "Falsche Zugangsdaten")

    token = create_token({"user_id": row["id"], "email": row["email"]})
    return {"access_token": token, "token_type": "bearer", "expires_in": ACCESS_TOKEN_EXPIRE_MIN}
