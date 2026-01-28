from pathlib import Path
from fastapi import FastAPI, Depends, Request
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .routers import auth, files, users
from .routers import transfers


settings = get_settings()
app = FastAPI(title=settings.app_name)


origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
# Ensure both localhost and 127.0.0.1 are allowed
if "http://localhost:5173" not in origins:
    origins.append("http://localhost:5173")
if "http://127.0.0.1:5173" not in origins:
    origins.append("http://127.0.0.1:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # Includes Authorization header
    expose_headers=["*"],
)

# Storage directory (relative to backend root unless absolute path is provided)
backend_root = Path(__file__).resolve().parents[1]  # .../backend/app -> .../backend
storage_dir = Path(settings.storage_dir)
if not storage_dir.is_absolute():
    storage_dir = backend_root / storage_dir
storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=storage_dir), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(transfers.router)


from .dependencies import get_current_user
from . import models, schemas


@app.get("/me", tags=["users"], response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return schemas.UserOut(
        id=user.id,
        email=user.email,
        created_at=user.created_at
    )


@app.get("/", tags=["health"])
def health():
    return {"status": "ok"}

@app.get("/health", tags=["health"])
def health_check():
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


@app.get("/debug/auth", tags=["debug"])
def debug_auth(request: Request):
    """
    DEV ONLY: Debug authentication state.
    Shows if Authorization header is present and token details.
    Call with: Authorization: Bearer <token> header
    """
    from .core.security import decode_access_token
    
    authorization = request.headers.get("Authorization")
    
    info = {
        "authorization_header_present": authorization is not None,
        "token_present": False,
        "token_valid": False,
        "token_decoded": None,
        "token_subject": None,
        "error": None
    }
    
    if authorization:
        # Extract Bearer token
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            info["token_present"] = True
            info["token_length"] = len(token)
            
            # Try to decode token
            payload = decode_access_token(token)
            if payload:
                info["token_valid"] = True
                info["token_decoded"] = {
                    "sub": payload.get("sub"),
                    "exp": payload.get("exp"),
                }
                info["token_subject"] = payload.get("sub")
            else:
                info["error"] = "Token is invalid or expired"
        else:
            info["error"] = "Authorization header must start with 'Bearer '"
            info["received_format"] = authorization[:20] + "..." if len(authorization) > 20 else authorization
    else:
        info["error"] = "No Authorization header provided"
        info["note"] = "Include header: Authorization: Bearer <token>"
    
    return info


@app.get("/debug/dbinfo", tags=["debug"])
def debug_dbinfo():
    """
    DEV ONLY: Detailed database connection information.
    Shows which database the backend is actually using.
    """
    from .database import engine, mask_password_in_url
    from .config import get_settings
    from sqlalchemy import text
    
    settings = get_settings()
    masked_url = mask_password_in_url(settings.database_url)
    
    info = {
        "database_url_masked": masked_url,
        "dialect": engine.dialect.name,
        "driver": engine.driver,
    }
    
    try:
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                # Get Postgres-specific info
                db_result = conn.execute(text("SELECT current_database()"))
                user_result = conn.execute(text("SELECT current_user"))
                version_result = conn.execute(text("SELECT version()"))
                count_result = conn.execute(text("SELECT COUNT(*) FROM users"))
                
                info.update({
                    "current_database": db_result.scalar(),
                    "current_user": user_result.scalar(),
                    "postgresql_version": version_result.scalar().split("\n")[0],
                    "users_count": count_result.scalar(),
                })
            elif engine.dialect.name == "sqlite":
                # Get SQLite-specific info
                count_result = conn.execute(text("SELECT COUNT(*) FROM users"))
                info.update({
                    "database_file": settings.database_url.replace("sqlite:///", ""),
                    "users_count": count_result.scalar(),
                    "warning": "Using SQLite instead of PostgreSQL!"
                })
    except Exception as e:
        info["error"] = str(e)
    
    return info


@app.post("/debug/test-user", tags=["debug"])
def debug_test_user():
    """
    DEV ONLY: Create a test user directly to verify database writes work.
    """
    from .database import get_db, SessionLocal
    from . import models
    from .core.security import hash_password as get_password_hash
    from sqlalchemy.orm import Session
    
    db = SessionLocal()
    try:
        test_email = "test@example.com"
        test_password = "testpassword123"
        
        # Check if test user exists
        existing = db.query(models.User).filter(models.User.email == test_email).first()
        if existing:
            return {
                "status": "exists",
                "message": f"Test user already exists with ID {existing.id}",
                "user_id": existing.id,
                "email": existing.email
            }
        
        # Create test user
        password_hash = get_password_hash(test_password)
        test_user = models.User(
            email=test_email,
            password_hash=password_hash,
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # Verify it was saved
        verify = db.query(models.User).filter(models.User.id == test_user.id).first()
        
        return {
            "status": "created",
            "message": "Test user created successfully",
            "user_id": test_user.id,
            "email": test_user.email,
            "verified": verify is not None,
            "total_users": db.query(models.User).count()
        }
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }
    finally:
        db.close()
