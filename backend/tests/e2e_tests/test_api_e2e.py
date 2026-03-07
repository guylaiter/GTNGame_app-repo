"""
E2E tests for the Guess the Number API.
Tests run against a live container instance.
"""
import requests
import pytest

BASE_URL = "http://localhost/api"


# ── Helper Functions ──────────────────────────────────────────────────────────

def cleanup_guess(name="E2ETest"):
    """Cleanup any existing guess before tests."""
    try:
        requests.delete(f"{BASE_URL}/guess", 
                       headers={"X-Test-Name": name})
    except:
        pass


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health_endpoint():
    """Verify health endpoint returns OK."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_submit_guess():
    """Test submitting a new guess."""
    cleanup_guess()
    
    payload = {"name": "E2ETest", "guess": 50}
    response = requests.post(f"{BASE_URL}/guess", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "E2ETest"
    assert data["guess"] == 50
    assert "distance" in data
    assert "percentile" in data


def test_leaderboard_contains_guess():
    """Verify leaderboard includes our submitted guess."""
    cleanup_guess()
    
    # Submit guess
    requests.post(f"{BASE_URL}/guess", 
                 json={"name": "E2ETest", "guess": 75})
    
    # Check leaderboard
    response = requests.get(f"{BASE_URL}/leaderboard")
    assert response.status_code == 200
    
    leaderboard = response.json()
    assert len(leaderboard) > 0
    
    # Find our entry
    our_entry = next((entry for entry in leaderboard 
                     if entry["name"] == "E2ETest"), None)
    assert our_entry is not None
    assert our_entry["guess"] == 75


def test_get_own_guess():
    """Test retrieving own guess."""
    cleanup_guess()
    
    # Submit guess
    requests.post(f"{BASE_URL}/guess", 
                 json={"name": "E2ETest", "guess": 60})
    
    # Retrieve it
    response = requests.get(f"{BASE_URL}/guess/me")
    assert response.status_code == 200
    
    data = response.json()
    assert data["exists"] is True
    assert data["name"] == "E2ETest"
    assert data["guess"] == 60


def test_get_guess_by_name():
    """Test retrieving guess by specific name."""
    cleanup_guess()
    
    # Submit guess
    requests.post(f"{BASE_URL}/guess", 
                 json={"name": "E2ETest", "guess": 85})
    
    # Retrieve by name
    response = requests.get(f"{BASE_URL}/guess/E2ETest")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "E2ETest"
    assert data["guess"] == 85
    assert "distance" in data


def test_delete_guess():
    """Test deleting own guess."""
    cleanup_guess()
    
    # Submit guess
    requests.post(f"{BASE_URL}/guess", 
                 json={"name": "E2ETest", "guess": 90})
    
    # Delete it
    response = requests.delete(f"{BASE_URL}/guess")
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()
    
    # Verify it's gone
    response = requests.get(f"{BASE_URL}/guess/me")
    data = response.json()
    assert data["exists"] is False


def test_full_user_flow():
    """Test complete user journey: submit → view → delete."""
    cleanup_guess()
    
    # 1. Submit guess
    response = requests.post(f"{BASE_URL}/guess", 
                            json={"name": "E2EFlowTest", "guess": 42})
    assert response.status_code == 201
    
    # 2. Check it appears in leaderboard
    response = requests.get(f"{BASE_URL}/leaderboard")
    leaderboard = response.json()
    assert any(entry["name"] == "E2EFlowTest" for entry in leaderboard)
    
    # 3. Retrieve own guess
    response = requests.get(f"{BASE_URL}/guess/me")
    assert response.json()["exists"] is True
    
    # 4. Delete guess
    response = requests.delete(f"{BASE_URL}/guess")
    assert response.status_code == 200
    
    # 5. Verify deletion
    response = requests.get(f"{BASE_URL}/guess/me")
    assert response.json()["exists"] is False
