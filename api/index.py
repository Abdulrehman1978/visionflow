from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch
import json
import logging
import time
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
CORS(app, supports_credentials=True) # Ensure credentials can be sent

# --- DATABASE CONFIGURATION ---
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Fallback to local SQLite
    database_url = "sqlite:///visionflow.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.String(200), nullable=False) # e.g., "Python_Basics_Variables"
    is_completed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.String(50), nullable=True) # Last watched timestamp in video
    last_watched = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize DB
with app.app_context():
    db.create_all()

# --- AUTH CONFIGURATION ---
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs'
)

# --- MOCK DATA ---
MOCK_SYLLABUS = {
    "title": "Python Mastery (Mock)",
    "modules": [
        {
            "title": "Basics",
            "topics": [
                { "name": "Variables & Data Types", "description": "Understanding numbers, strings, and booleans." },
                { "name": "Control Flow", "description": "If statements, loops, and logic." },
                { "name": "Functions", "description": "Defining and calling reusable code blocks." }
            ]
        },
        {
            "title": "Intermediate",
            "topics": [
                { "name": "Object-Oriented Programming", "description": "Classes, objects, and inheritance." },
                { "name": "File Handling", "description": "Reading and writing files." },
                { "name": "Error Handling", "description": "Try/Except blocks and exceptions." }
            ]
        },
        {
            "title": "Real-world Libraries",
            "topics": [
                { "name": "Pandas", "description": "Data manipulation and analysis." },
                { "name": "Flask", "description": "Building web applications." },
                { "name": "Requests", "description": "Making HTTP requests." }
            ]
        }
    ]
}

# 1. Setup Gemini (New Client)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")

# --- AUTH ROUTES ---
@app.route('/api/auth/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/callback')
def authorize():
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        
        # Check if user exists
        user = User.query.filter_by(google_id=user_info['id']).first()
        if not user:
            user = User(
                google_id=user_info['id'], 
                email=user_info['email'],
                name=user_info.get('name'),
                avatar=user_info.get('picture')
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        # Redirect to frontend dashboard
        return redirect(os.getenv("FRONTEND_URL", "/dashboard"))
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/auth/me')
def current_user_info():
    if current_user.is_authenticated:
        return jsonify({
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "avatar": current_user.avatar
        })
    return jsonify(None), 401

# --- PROGRESS ROUTES ---
@app.route('/api/progress/update', methods=['POST'])
@login_required
def update_progress():
    data = request.json
    topic_id = data.get('topic_id')
    is_completed = data.get('is_completed', False)
    timestamp = data.get('timestamp')
    
    if not topic_id:
        return jsonify({"error": "Topic ID required"}), 400

    progress = UserProgress.query.filter_by(user_id=current_user.id, topic_id=topic_id).first()
    
    if progress:
        progress.is_completed = is_completed
        progress.timestamp = timestamp
        progress.last_watched = datetime.utcnow()
    else:
        progress = UserProgress(
            user_id=current_user.id,
            topic_id=topic_id,
            is_completed=is_completed,
            timestamp=timestamp
        )
        db.session.add(progress)
    
    db.session.commit()
    return jsonify({"message": "Progress updated"})

@app.route('/api/progress', methods=['GET'])
@login_required
def get_progress():
    # Return list of completed topic IDs
    completed_progress = UserProgress.query.filter_by(user_id=current_user.id, is_completed=True).all()
    completed_ids = [p.topic_id for p in completed_progress]
    return jsonify(completed_ids)


@app.route('/api/syllabus', methods=['GET'])
def get_syllabus():
    language = request.args.get('language', 'Python')
    
    # Smart Prompt for Syllabus
    prompt = f"""
    Create a structured learning syllabus for {language}.
    Return ONLY valid JSON. Do not use Markdown blocks.
    Structure:
    {{
        "title": "{language} Mastery",
        "modules": [
            {{
                "title": "Module Title (e.g., Basics)",
                "topics": [
                    {{ "name": "Topic Name", "description": "Short explanation" }}
                ]
            }}
        ]
    }}
    Include 3 modules: Basics, Intermediate, and Real-world Libraries.
    """
    
    try:
        if not client:
             raise Exception("Gemini Client not initialized")

        # New API Call Syntax with gemini-1.5-flash
        response = client.models.generate_content(
            model='gemini-1.5-flash', 
            contents=prompt
        )
        
        # Clean response text
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        syllabus_data = json.loads(clean_text)
        return jsonify(syllabus_data)

    except Exception as e:
        logger.warning(f"⚠️ API Error: {e}. Serving Mock Data.")
        # Return Mock Data on ANY error (Rate Limit, Network, etc.)
        return jsonify(MOCK_SYLLABUS)

@app.route('/api/videos', methods=['GET'])
def get_videos():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"error": "Topic required"}), 400

    print(f"🔎 Searching for: {topic}")
    
    # 1. Search YouTube
    try:
        results = YoutubeSearch(f"{topic} tutorial", max_results=5).to_dict()
    except Exception as e:
        return jsonify({"error": f"YouTube search failed: {str(e)}"}), 500
    
    scored_videos = []
    
    # 2. Analyze Transcripts (Try/Except block for fallback)
    for video in results:
        video_id = video['id']
        rating = "5" # Default rating
        
        try:
             if not client:
                 raise Exception("Gemini Client not initialized")

             # Fetch transcript
             transcript = YouTubeTranscriptApi.get_transcript(video_id)
             full_text = " ".join([t['text'] for t in transcript])[:2000] 
            
             # Analyze with Gemini
             analysis_prompt = f"""
             Rate this video transcript for learning "{topic}" on a scale of 1-10.
             Transcript start: "{full_text}..."
             Return ONLY the number.
             """
             rating_response = client.models.generate_content(
                model='gemini-1.5-flash', 
                contents=analysis_prompt
             )
             rating_text = rating_response.text.strip()
             if rating_text.isdigit():
                 rating = rating_text

        except Exception as e:
            # If Gemini fails (rate limit, etc) or transcript fails, just continue with default score
            logger.warning(f"Skipping AI rating for video {video_id}: {e}")
            pass

        scored_videos.append({
            "id": video_id,
            "title": video['title'],
            "thumbnail": video['thumbnails'][0],
            "score": int(rating)
        })

    # 3. Sort by Score
    scored_videos.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify(scored_videos[:3])

if __name__ == '__main__':
    app.run(port=3000, debug=True)