import os
import pytest

# Override DB URL before importing app — must be before any app import
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_NUMBER"] = "42"

from app import app, db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a test client with a fresh in-memory SQLite database."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


# ── GET /health ────────────────────────────────────────────────────────────────

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


# ── GET /api/leaderboard ───────────────────────────────────────────────────────

def test_leaderboard_empty(client):
    res = client.get("/api/leaderboard")
    assert res.status_code == 200
    assert res.get_json() == []


def test_leaderboard_with_entries(client):
    client.post("/api/guess", json={"name": "Alice", "guess": 75})
    client.post("/api/guess", json={"name": "Bob", "guess": 50},
                headers={"X-Forwarded-For": "9.9.9.9"})
    res = client.get("/api/leaderboard")
    data = res.get_json()
    assert res.status_code == 200
    assert len(data) == 2
    assert data[0]["rank"] == 1


# ── POST /api/guess ────────────────────────────────────────────────────────────

def test_submit_guess_success(client):
    res = client.post("/api/guess", json={"name": "Alice", "guess": 75})
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "Alice"
    assert data["guess"] == 75
    assert "distance" in data
    assert "percentile" in data


def test_submit_guess_missing_fields(client):
    res = client.post("/api/guess", json={"name": "Alice"})
    assert res.status_code == 400


def test_submit_guess_duplicate_name(client):
    client.post("/api/guess", json={"name": "Alice", "guess": 75})
    res = client.post("/api/guess", json={"name": "Alice", "guess": 80})
    assert res.status_code == 409


def test_submit_guess_invalid_number(client):
    res = client.post("/api/guess", json={"name": "Alice", "guess": "abc"})
    assert res.status_code == 400


# ── GET /api/guess/me ──────────────────────────────────────────────────────────

def test_get_my_guess_exists(client):
    client.post("/api/guess", json={"name": "Alice", "guess": 75})
    res = client.get("/api/guess/me")
    assert res.status_code == 200
    data = res.get_json()
    assert data["exists"] is True
    assert data["name"] == "Alice"


def test_get_my_guess_not_found(client):
    res = client.get("/api/guess/me")
    assert res.status_code == 200
    assert res.get_json() == {"exists": False}


# ── GET /api/guess/<name> ──────────────────────────────────────────────────────

def test_get_guess_found(client):
    client.post("/api/guess", json={"name": "Alice", "guess": 75})
    res = client.get("/api/guess/Alice")
    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Alice"
    assert data["guess"] == 75
    assert data["distance"] == 33


def test_get_guess_not_found(client):
    res = client.get("/api/guess/Unknown")
    assert res.status_code == 404


# ── DELETE /api/guess ──────────────────────────────────────────────────────────

def test_delete_guess_success(client):
    client.post("/api/guess", json={"name": "Alice", "guess": 75})
    res = client.delete("/api/guess")
    assert res.status_code == 200
    assert "deleted" in res.get_json()["message"]


def test_delete_guess_not_found(client):
    res = client.delete("/api/guess")
    assert res.status_code == 404

