import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture(scope="session")
def test_env(tmp_path_factory):
    """
    Configure a lightweight test environment:
    - SQLite DB (file)
    - Temp storage directory (no writes to repo)
    """
    tmpdir = tmp_path_factory.mktemp("fs_tests")
    db_path = tmpdir / "test.db"
    storage_dir = tmpdir / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    os.environ["ENV"] = "test"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_EXPIRES_MINUTES"] = "60"
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:5173"
    os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
    os.environ["STORAGE_DIR"] = str(storage_dir)

    return {"db_path": db_path, "storage_dir": storage_dir}


@pytest.fixture(scope="session")
def app_context(test_env):
    """
    Import the FastAPI app once (after env is set) and prepare DB schema.
    Avoid module reloads to prevent SQLAlchemy metadata duplication.
    """
    import app.config as config
    config.get_settings.cache_clear()

    import app.database as database
    import app.models as models

    models.Base.metadata.create_all(bind=database.engine)

    import app.main as main
    return {"app": main.app, "database": database, "models": models}


@pytest.fixture
def client(app_context):
    return TestClient(app_context["app"])


@pytest.fixture
def db_session(app_context):
    """
    Provide a DB session bound to the test database engine.
    """
    database = app_context["database"]
    session = database.SessionLocal()
    # Clean slate for each test
    try:
        session.execute(text("DELETE FROM files"))
        session.execute(text("DELETE FROM users"))
        session.commit()
        yield session
    finally:
        session.close()
