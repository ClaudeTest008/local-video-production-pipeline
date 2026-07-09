"""Test env must be configured before app import — settings load at import time."""

import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="lvpp-test-"))
os.environ["LVPP_DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ["LVPP_PROJECTS_ROOT"] = str(_tmp / "projects")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # context manager runs lifespan → init_db
        yield c


@pytest.fixture()
def project(client):
    resp = client.post("/api/projects", json={"name": "Test Video", "idea": "test idea"})
    assert resp.status_code == 201
    return resp.json()
