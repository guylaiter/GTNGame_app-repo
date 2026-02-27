import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Create a test client with a mocked DB."""
    with patch("app.db"):
        from app import app
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client


def make_guess(name="Alice", ip="1.2.3.4", guess=75, distance=33):
    """Helper to create a mock Guess object."""
    mock = MagicMock()
    mock.name = name
    mock.ip_address = ip
    mock.guess = guess
    mock.distance = distance
    mock.created_at = datetime(2024, 1, 1, 12, 0)
    return mock


# ── GET /health ────────────────────────────────────────────────────────────────

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


# ── GET /api/leaderboard ───────────────────────────────────────────────────────

def test_leaderboard_empty(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.order_by.return_value.limit.return_value.all.return_value = []
        res = client.get("/api/leaderboard")
        assert res.status_code == 200
        assert res.get_json() == []


def test_leaderboard_with_entries(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.order_by.return_value.limit.return_value.all.return_value = [
            make_guess("Alice", guess=75, distance=33),
            make_guess("Bob", guess=50, distance=8),
        ]
        res = client.get("/api/leaderboard")
        data = res.get_json()
        assert res.status_code == 200
        assert len(data) == 2
        assert data[0]["rank"] == 1
        assert data[0]["name"] == "Alice"


# ── POST /api/guess ────────────────────────────────────────────────────────────

def test_submit_guess_success(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = None
        MockGuess.query.count.return_value = 1
        MockGuess.query.filter.return_value.count.return_value = 1

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
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = make_guess()
        res = client.post("/api/guess", json={"name": "Alice", "guess": 75})
        assert res.status_code == 409


def test_submit_guess_invalid_number(client):
    res = client.post("/api/guess", json={"name": "Alice", "guess": "abc"})
    assert res.status_code == 400


# ── GET /api/guess/<name> ──────────────────────────────────────────────────────

def test_get_guess_found(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = make_guess()
        res = client.get("/api/guess/Alice")
        assert res.status_code == 200
        data = res.get_json()
        assert data["name"] == "Alice"
        assert data["guess"] == 75
        assert data["distance"] == 33


def test_get_guess_not_found(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = None
        res = client.get("/api/guess/Unknown")
        assert res.status_code == 404


# ── GET /api/guess/me ──────────────────────────────────────────────────────────

def test_get_my_guess_exists(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = make_guess()
        res = client.get("/api/guess/me")
        assert res.status_code == 200
        data = res.get_json()
        assert data["exists"] is True
        assert data["name"] == "Alice"


def test_get_my_guess_not_found(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = None
        res = client.get("/api/guess/me")
        assert res.status_code == 200
        assert res.get_json() == {"exists": False}


# ── DELETE /api/guess ──────────────────────────────────────────────────────────

def test_delete_guess_success(client):
    with patch("app.Guess") as MockGuess:
        with patch("app.db") as MockDB:
            MockGuess.query.filter_by.return_value.first.return_value = make_guess()
            res = client.delete("/api/guess")
            assert res.status_code == 200
            assert "deleted" in res.get_json()["message"]


def test_delete_guess_not_found(client):
    with patch("app.Guess") as MockGuess:
        MockGuess.query.filter_by.return_value.first.return_value = None
        res = client.delete("/api/guess")
        assert res.status_code == 404