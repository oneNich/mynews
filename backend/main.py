import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from db import engine, SessionLocal
from models import Base
from worker import main as run_job

app = FastAPI()


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/stories")
def get_stories():
    return []


@app.post("/admin/collect")
def collect(x_admin_token: str = Header(None)):
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token or x_admin_token != admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    run_job(trigger="manual")
    return {"status": "ok"}
