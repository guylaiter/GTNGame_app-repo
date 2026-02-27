# 🎯 Guess The Number — Docker 3-Tier App

A fun number guessing game built with Flask, PostgreSQL, and Nginx.

## Architecture

```
[Browser] → [Nginx :80] → [Flask :5000] → [PostgreSQL :5432]
```

- **Tier 1 (Frontend):** Nginx serving static HTML/CSS/JS
- **Tier 2 (Backend):** Flask REST API
- **Tier 3 (Database):** PostgreSQL

### Networks
- `backend_network` — db + backend (backend talks to db)
- `frontend_network` — backend + frontend (nginx proxies to backend)

## Setup & Run

### 1. Create a `.env` file in the project root
```
SECRET_NUMBER=42
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=guessdb
DATABASE_URL=postgresql://postgres:postgres@db:5432/guessdb
```

### 2. Start the app
```bash
docker-compose up --build
```

### 3. Open your browser
```
http://localhost
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/guess` | Submit a guess |
| GET | `/api/guess/me` | Get your own guess by IP |
| GET | `/api/guess/<name>` | Get a specific guess by name |
| DELETE | `/api/guess` | Delete your guess (by IP) |
| GET | `/api/leaderboard` | Get top 20 guesses |

### POST /api/guess
**Body:**
```json
{ "name": "Alice", "guess": 75 }
```
**Response:**
```json
{
  "name": "Alice",
  "guess": 75,
  "distance": 33,
  "percentile": 82,
  "message": "You were 33 away from the target!"
}
```

### GET /api/guess/me
Returns the guess associated with the requester's IP address.

**Response (exists):**
```json
{ "exists": true, "name": "Alice", "guess": 75, "distance": 33 }
```
**Response (not found):**
```json
{ "exists": false }
```

### GET /api/guess/\<name\>
**Response:**
```json
{
  "name": "Alice",
  "guess": 75,
  "distance": 33,
  "created_at": "2024-01-01 12:00"
}
```

### DELETE /api/guess
Deletes the guess associated with the requester's IP address.

**Response:**
```json
{ "message": "Guess by 'Alice' deleted successfully" }
```

## Anti-Cheat
- One guess per name (case-sensitive)
- One guess per IP address
- Both checks enforced at the database level

## Stop the app
```bash
docker-compose down
# To also remove the database volume:
docker-compose down -v
```
