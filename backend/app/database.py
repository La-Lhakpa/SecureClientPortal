from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import urlparse
from .config import get_settings


settings = get_settings()

# Parse and mask password in DATABASE_URL for logging
def mask_password_in_url(url: str) -> str:
    """Mask password in database URL for safe logging"""
    try:
        parsed = urlparse(url)
        if parsed.password:
            # Replace password with ***
            netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return f"{parsed.scheme}://{netloc}{parsed.path}"
        return url
    except Exception:
        return "***"

# Log database connection info on startup
masked_url = mask_password_in_url(settings.database_url)
print(f"[DATABASE] Connecting to: {masked_url}")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=False,  # Set to True for SQL query logging
)

# Verify connection and log dialect
try:
    with engine.connect() as conn:
        dialect_name = engine.dialect.name
        print(f"[DATABASE] Engine created successfully. Dialect: {dialect_name}")
        if dialect_name == "postgresql":
            # Get Postgres-specific info
            result = conn.execute(text("SELECT current_database(), current_user, version()"))
            row = result.fetchone()
            if row:
                db_name, db_user, db_version = row[0], row[1], row[2].split("\n")[0]
                print(f"[DATABASE] Connected to PostgreSQL database: {db_name}")
                print(f"[DATABASE] Connected as user: {db_user}")
                print(f"[DATABASE] PostgreSQL version: {db_version}")
        elif dialect_name == "sqlite":
            print(f"[DATABASE] WARNING: Using SQLite instead of PostgreSQL!")
except Exception as e:
    print(f"[DATABASE] ERROR: Failed to connect: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to get database session. Ensures proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
