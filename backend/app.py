import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/guessdb")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

SECRET_NUMBER = int(os.environ.get("SECRET_NUMBER", 42))

db = SQLAlchemy(app)


class Guess(db.Model):
    __tablename__ = "guesses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    guess = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


with app.app_context():
    db.create_all()

@app.route("/api/guess/me", methods=["GET"])
def get_my_guess():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    guess = Guess.query.filter_by(ip_address=ip).first()
    if not guess:
        return jsonify({"exists": False}), 200

    return jsonify({
        "exists": True,
        "name": guess.name,
        "guess": guess.guess,
        "distance": guess.distance
    }), 200

@app.route("/api/guess/<name>", methods=["GET"])
def get_guess(name):
    guess = Guess.query.filter_by(name=name).first()
    if not guess:
        return jsonify({"error": "Name not found"}), 404
    return jsonify({
        "name": guess.name,
        "guess": guess.guess,
        "distance": guess.distance,
        "created_at": guess.created_at.strftime("%Y-%m-%d %H:%M")
    })

@app.route("/api/guess", methods=["POST"])
def submit_guess():
    data = request.get_json()
    name = data.get("name", "").strip()
    guess_value = data.get("guess")

    if not name or guess_value is None:
        return jsonify({"error": "Name and guess are required"}), 400

    try:
        guess_value = int(guess_value)
    except (ValueError, TypeError):
        return jsonify({"error": "Guess must be a number"}), 400

    # Get real IP (handle proxy)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    # Check name already exists
    if Guess.query.filter_by(name=name).first():
        return jsonify({"error": "This name has already guessed!"}), 409

    # Check IP already exists
    if Guess.query.filter_by(ip_address=ip).first():
        return jsonify({"error": "This IP has already guessed!"}), 409

    distance = abs(guess_value - SECRET_NUMBER)
    new_guess = Guess(name=name, ip_address=ip, guess=guess_value, distance=distance)
    db.session.add(new_guess)
    db.session.commit()

    # Calculate rank among all guesses
    total = Guess.query.count()
    better_or_equal = Guess.query.filter(Guess.distance <= distance).count()
    rank = better_or_equal
    percentile = round((1 - (rank - 1) / total) * 100) if total > 0 else 100

    return jsonify({
        "name": name,
        "guess": guess_value,
        "distance": distance,
        "percentile": percentile,
        "message": f"You were {distance} away from the target!"
    }), 201


@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    top = Guess.query.order_by(Guess.distance.asc()).limit(20).all()
    results = []
    for i, g in enumerate(top):
        results.append({
            "rank": i + 1,
            "name": g.name,
            "distance": g.distance,
            "created_at": g.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return jsonify(results)

@app.route("/api/guess", methods=["DELETE"])
def delete_guess():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    guess = Guess.query.filter_by(ip_address=ip).first()
    if not guess:
        return jsonify({"error": "No guess found for your IP"}), 404

    db.session.delete(guess)
    db.session.commit()
    return jsonify({"message": f"Guess by '{guess.name}' deleted successfully"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
