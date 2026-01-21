from pathlib import Path
from fastapi import FastAPI, Depends
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import get_settings
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

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)


from .dependencies import get_current_user


@app.get("/me", tags=["users"])
def me(user=Depends(get_current_user)):
    return user


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def health_db():
    """
    Quick DB connectivity check (helps debug 'register not working' issues).
    """
    from .database import engine

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"db": "ok", "dialect": engine.dialect.name}
