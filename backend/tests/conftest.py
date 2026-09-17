import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _disable_celery_dispatch(monkeypatch):
    """全局屏蔽 Celery 投递（测试环境没有 broker/Redis）。

    不屏蔽时 ``task.delay()`` 会对不可达的 broker 反复重试，
    导致 ``test_detection.py`` 挂死、全量测试跑不完
    （见 docs/tech/09-测试体系.md §19.3、14-评估与改进.md P0-4）。
    需要验证「投递失败」路径的用例可在测试内覆盖本 fixture。
    """
    monkeypatch.setattr(
        "app.tasks.detection.detect_anomaly_for_log.delay", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "app.tasks.email.send_alert_email.delay", lambda *a, **k: None
    )


@pytest.fixture(scope="function")
def engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    e = create_engine(url, echo=False)
    Base.metadata.create_all(bind=e)
    yield e
    e.dispose()
    try:
        os.unlink(path)
    except PermissionError:
        pass


@pytest.fixture(scope="function")
def client(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db(engine):
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
