import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .database import engine, Base
from .routers import auth, files, users


settings = get_settings()
app = FastAPI(title=settings.app_name)


origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage_dir = Path("storage")
storage_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=storage_dir), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}
