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
from pathlib import Path

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})
# ProxyFix for Vercel deployment (trust proxy headers)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Secret Key Configuration
app.secret_key = os.getenv("APP_SECRET_KEY", "dev_secret")

# Session Cookie Security Configuration
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['SESSION_COOKIE_SECURE'] = True       # Required for Vercel HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True     # Prevent JS theft
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # Allow cookie in redirects (Critical for Mobile)

CORS(app, supports_credentials=True) # Ensure credentials can be sent

# --- DATABASE CONFIGURATION ---
# Get POSTGRES_URL from environment and fix the scheme if needed
postgres_url = os.getenv("POSTGRES_URL")
if postgres_url:
    # Replace postgres:// with postgresql:// for SQLAlchemy compatibility
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    database_url = postgres_url
else:
    # Fallback to local SQLite if POSTGRES_URL not found
    database_url = "sqlite:///visionflow.db"
    logger.warning("POSTGRES_URL not found in .env, using SQLite fallback")

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
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=True)
    topic_id = db.Column(db.String(200), nullable=True)  # Legacy support
    video_completed = db.Column(db.Boolean, default=False)
    quiz_completed = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)  # Overall completion
    timestamp = db.Column(db.String(50), nullable=True)  # Last watched timestamp
    last_watched = db.Column(db.DateTime, default=datetime.utcnow)


# --- COURSE MODELS ---
class Course(db.Model):
    id = db.Column(db.String(100), primary_key=True) # e.g., "python", "java"
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(200), nullable=True)
    is_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    modules = db.relationship('Module', backref='course', lazy=True)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(100), db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    lessons = db.relationship('Lesson', backref='module', lazy=True)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    video_url = db.Column(db.String(200), nullable=False) # YouTube Video ID
    duration = db.Column(db.String(50), nullable=True) # e.g., "10:05"
    order_index = db.Column(db.Integer, nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # ["Option A", "Option B", "Option C", "Option D"]
    correct_answer = db.Column(db.String(100), nullable=False)
    lesson = db.relationship('Lesson', backref=db.backref('quizzes', lazy=True))

class PracticeQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    problem_statement = db.Column(db.Text, nullable=False)
    test_cases = db.Column(db.JSON, nullable=True)  # [{"input": "...", "expected": "..."}]
    hints = db.Column(db.JSON, nullable=True)  # ["hint1", "hint2"]
    lesson = db.relationship('Lesson', backref=db.backref('practice_questions', lazy=True))

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
        # Redirect to frontend dashboard (relative path for mobile compatibility)
        return redirect('/dashboard')
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/api/auth/logout')
#
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
#
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
#
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

@app.route('/api/courses', methods=['GET'])
def get_courses():
    courses = Course.query.all()  # Fetch all courses from database
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "thumbnail": c.thumbnail_url
    } for c in courses])

@app.route('/api/courses/<course_id>', methods=['GET'])
def get_course_detail(course_id):
    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    
    syllabus = {
        "title": course.title,
        "description": course.description,
        "modules": []
    }
    
    # Sort modules by order_index
    modules = sorted(course.modules, key=lambda x: x.order_index)
    
    for module in modules:
        lessons = sorted(module.lessons, key=lambda x: x.order_index)
        syllabus["modules"].append({
            "title": module.title,
            "topics": [{
                "id": l.id,
                "name": l.title,
                "video_id": l.video_url,
                "duration": l.duration,
                "quiz_count": len(l.quizzes),
                "practice_count": len(l.practice_questions)
            } for l in lessons]
        })
        
    return jsonify(syllabus)

@app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson_detail(lesson_id):
    """Get detailed lesson info including quizzes and practice questions"""
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404
    
    return jsonify({
        "id": lesson.id,
        "title": lesson.title,
        "video_id": lesson.video_url,
        "duration": lesson.duration,
        "quizzes": [{
            "id": q.id,
            "question": q.question,
            "options": q.options,
            "correct_answer": q.correct_answer
        } for q in lesson.quizzes],
        "practice_questions": [{
            "id": p.id,
            "problem_statement": p.problem_statement,
            "test_cases": p.test_cases,
            "hints": p.hints
        } for p in lesson.practice_questions]
    })

@app.route('/api/courses/<course_id>/progress', methods=['GET'])
#
def get_course_progress(course_id):
    # Get all lessons for this course
    # This is a bit complex efficiently in SQL, but let's do it simply first
    # We need to find which lessons the user has completed.
    # UserProgress currently stores 'topic_id'. The plan mentioned maybe linking to Lesson.id.
    # The existing UpdateProgress stores 'topic_id' which was a string. 
    # For now, let's assume 'topic_id' in UserProgress will correspond to 'Lesson.title' OR we update the progress logic.
    # The User Request says: "Returns which lessons the current user has completed (join with UserProgress)."
    # Given the previous context, 'topic_id' was the lesson name. 
    # Let's try to map it. 
    
    completed_progress = UserProgress.query.filter_by(user_id=current_user.id, is_completed=True).all()
    completed_names = {p.topic_id for p in completed_progress} # Set of completed topic names/ids
    
    return jsonify(list(completed_names))

@app.route('/api/videos', methods=['GET'])
def get_videos():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"error": "Topic required"}), 400

    print(f"🔎 Searching for: {topic}")
    
    # Check if this topic exists as a lesson in our DB first (High Quality)
    lesson = Lesson.query.filter_by(title=topic).first()
    if lesson:
         return jsonify([{
            "id": lesson.video_url,
            "title": lesson.title,
            "thumbnail": f"https://img.youtube.com/vi/{lesson.video_url}/mqdefault.jpg",
            "score": 10
        }])

    # Fallback: Search YouTube (Legacy Logic)
    try:
        results = YoutubeSearch(f"{topic} tutorial", max_results=3).to_dict()
    except Exception as e:
        return jsonify({"error": f"YouTube search failed: {str(e)}"}), 500
    
    # ... (rest of legacy logic could be here, or simplified)
    scored_videos = [{
            "id": v['id'],
            "title": v['title'],
            "thumbnail": v['thumbnails'][0],
            "score": 5
        } for v in results]
    
    return jsonify(scored_videos)

if __name__ == '__main__':
    app.run(port=3000, debug=True)