from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
# Configure local SQLite database
import os

# If running on Render, use a dynamic memory database; otherwise, use local file
if os.environ.get('RENDER'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///space_pew.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    matches = db.relationship('Match', backref='player', lazy=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    played_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


@app.route('/api/submit-score', methods=['POST'])
def submit_score():
    """Saves a final match score for a player."""
    data = request.get_json()
    username = data.get('username', '').strip()
    score = data.get('score')

    if not username or score is None:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    new_match = Match(user_id=user.id, score=score)
    db.session.add(new_match)
    db.session.commit()

    return jsonify({"status": "success", "message": f"Saved score {score} for {username}"}), 200


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Returns top 10 unique player high scores as raw data."""
    subquery = db.session.query(
        Match.user_id, 
        db.func.max(Match.score).label('max_score')
    ).group_by(Match.user_id).subquery()

    top_scores = db.session.query(User.username, subquery.c.max_score).\
        join(subquery, User.id == subquery.c.user_id).\
        order_by(subquery.c.max_score.desc()).limit(10).all()

    leaderboard_data = [{"username": row[0], "score": row[1]} for row in top_scores]
    return jsonify(leaderboard_data), 200



@app.route('/leaderboard')
def show_web_leaderboard():
    """Renders a beautiful web dashboard UI for the leaderboard."""
    subquery = db.session.query(
        Match.user_id, 
        db.func.max(Match.score).label('max_score')
    ).group_by(Match.user_id).subquery()

    top_scores = db.session.query(User.username, subquery.c.max_score).\
        join(subquery, User.id == subquery.c.user_id).\
        order_by(subquery.c.max_score.desc()).limit(10).all()

    leaderboard_data = [{"username": row[0], "score": row[1]} for row in top_scores]
    
    return render_template('leaderboard.html', leaderboard=leaderboard_data)


@app.route('/match-history/<username>')
def show_match_history(username):
    """Renders a tactical Pilot Log UI for a specific player's history."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return "<h1>Pilot Not Found in Database</h1>", 404

    matches = Match.query.filter_by(user_id=user.id).\
        order_by(Match.played_at.desc()).limit(15).all()

    history_data = []
    for m in matches:
        wat_time = m.played_at + timedelta(hours=1) 
        history_data.append({
            "score": m.score, 
            "date": wat_time.strftime('%b %d, %Y'),
            "time": wat_time.strftime('%H:%M')
        })
    
    return render_template('history.html', username=username, history=history_data)


if __name__ == '__main__':
    app.run(debug=True, port=5000)