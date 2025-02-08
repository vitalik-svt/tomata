from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_test():
    assert 1 == 1