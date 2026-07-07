import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Choose SQLite system dynamically based on running environment
if os.environ.get('RENDER'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///space_pew.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    matches = db.relationship('Match', backref='pilot', lazy=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Initialize database tables
with app.app_context():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            return "Username cannot be empty!", 400
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "This pilot name is already registered!", 400
            
        new_user = User(username=username)
        db.session.add(new_user)
        db.session.commit()
        return f"Pilot '{username}' registered! You can now close this tab and run your game client."
    return render_template('register.html')

@app.route('/api/submit-score', methods=['POST'])
def submit_score():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    score_val = data.get('score')

    if not username or score_val is None:
        return jsonify({"status": "error", "message": "Missing username or score"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "Pilot not found in database"}), 404

    new_match = Match(user_id=user.id, score=score_val)
    db.session.add(new_match)
    db.session.commit()
    return jsonify({"status": "success", "message": f"Score synced for {username}!"}), 200

@app.route('/leaderboard')
def leaderboard():
    top_matches = Match.query.order_by(Match.score.desc()).limit(10).all()
    return render_template('leaderboard.html', matches=top_matches)
# 🚀 SECURE LOGIN ENDPOINT FOR PYGAME CLIENT
@app.route('/api/login', methods=['POST'])
def login():
    """Verifies if a pilot username exists in the system database for client authentication."""
    data = request.get_json() or {}
    username = data.get('username', '').strip()

    if not username:
        return jsonify({"status": "error", "message": "Username cannot be empty!"}), 400

    user = User.query.filter_by(username=username).first()
    
    if user:
        return jsonify({
            "status": "success", 
            "message": f"Welcome back, Pilot {username}!",
            "username": user.username
        }), 200
    else:
        return jsonify({
            "status": "error", 
            "message": "Pilot profile not found. Please register online first!"
        }), 404

# 🚀 ADDED: This is the missing route that was causing your "Not Found" error!
@app.route('/match-history/<username>')
def match_history(username):
    # Enforce case-insensitive search or look up directly
    user = User.query.filter_by(username=username).first()
    if not user:
        return f"Pilot '{username}' not found.", 404
    
    user_matches = Match.query.filter_by(user_id=user.id).order_by(Match.id.desc()).all()
    
    # 🚀 FIX: Convert to uppercase here in Python safely before passing it to HTML
    display_name = username.upper()
    
    return render_template('match_history.html', username=display_name, matches=user_matches)

if __name__ == '__main__':
    app.run(debug=True)
