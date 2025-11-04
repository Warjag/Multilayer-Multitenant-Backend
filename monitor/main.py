import os
import time
import threading
import json
from datetime import datetime, timezone

import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# -------------------------
# Konfiguration über ENV
# -------------------------
API_BASE = os.getenv("MON_API_BASE", "http://api:8000")  # im Compose-Netz heißt der API-Service "api"
CHECK_INTERVAL_SEC = int(os.getenv("MON_INTERVAL_SEC", "60"))
LOG_PATH = os.getenv("MON_LOG_PATH", "/logs/monitor.log")

# In-Memory Status
last_result = {
    "timestamp": None,
    "status": "unknown",
    "checks": {},
    "error": None,
}

app = FastAPI(title="IHK Monitoring", version="0.1.0")

def _log(line: str):
    # Logzeile mit Zeitstempel
    stamp = datetime.now(timezone.utc).isoformat()
    msg = f"[{stamp}] {line}"
    print(msg, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"[monitor] Konnte Log nicht schreiben: {e}", flush=True)

def run_health_check():
    """Einmaliger Health-Check gegen die API."""
    global last_result
    url = f"{API_BASE}/health"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        last_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": data.get("status", "unknown"),
            "checks": data.get("checks", {}),
            "error": None,
        }
        _log(f"HealthCheck OK: status={last_result['status']} checks={json.dumps(last_result['checks'])}")
    except Exception as e:
        last_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "checks": {},
            "error": str(e),
        }
        _log(f"HealthCheck ERROR: {e}")

def _loop():
    # Initiale kleine Wartezeit, damit API hochfahren kann
    time.sleep(5)
    while True:
        run_health_check()
        time.sleep(CHECK_INTERVAL_SEC)

# Hintergrund-Thread starten, sobald die App läuft
def start_background_loop():
    t = threading.Thread(target=_loop, daemon=True)
    t.start()

# -------------------------
# FastAPI Endpoints
# -------------------------

class RunNowOut(BaseModel):
    ok: bool
    last: dict

@app.on_event("startup")
def _on_startup():
    _log("Monitoring-App startet. Ziel-API: " + API_BASE)
    start_background_loop()

@app.get("/live")
def live():
    return {"ok": True, "service": "monitor", "time": datetime.now(timezone.utc).isoformat()}

@app.get("/health-check/last")
def health_last():
    return last_result

@app.post("/health-check/run-now", response_model=RunNowOut)
def health_run_now():
    run_health_check()
    return RunNowOut(ok=True, last=last_result)

if __name__ == "__main__":
    # Lokaler Start (für Tests). Im Container übernimmt CMD den Start.
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=False)
