from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch
import json
import logging
import time
import traceback
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


# --- COURSE MODELS ---
class Course(db.Model):
    id = db.Column(db.String(100), primary_key=True) # e.g., "python", "java"
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(200), nullable=True)
    level = db.Column(db.String(50), nullable=True) # e.g., "Beginner", "Intermediate", "Advanced"
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

        # New API Call Syntax with stable gemini-pro
        response = client.models.generate_content(
            model='gemini-pro', 
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
    courses = Course.query.all()  # Fetch all courses including AI-generated
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "thumbnail": c.thumbnail_url,
        "level": c.level,
        "is_generated": c.is_generated
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
            "topics": [{ # Mapping 'lessons' to 'topics' to match frontend expectation or updating frontend? Plan says update frontend to structured syllabus.
                "id": l.id,
                "name": l.title,
                "video_id": l.video_url,
                "duration": l.duration
            } for l in lessons]
        })
        
    return jsonify(syllabus)


@app.route('/api/courses/<course_id>/progress', methods=['GET'])
@login_required
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

@app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson_detail(lesson_id):
    """Get lesson details including video URL and next lesson ID"""
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({"error": "Lesson not found"}), 404
    
    # Get the module this lesson belongs to
    module = Module.query.get(lesson.module_id)
    if not module:
        return jsonify({"error": "Module not found"}), 404
    
    # Find the next lesson
    next_lesson_id = None
    
    # First, try to find next lesson in same module
    next_in_module = Lesson.query.filter(
        Lesson.module_id == lesson.module_id,
        Lesson.order_index > lesson.order_index
    ).order_by(Lesson.order_index.asc()).first()
    
    if next_in_module:
        next_lesson_id = next_in_module.id
    else:
        # Look for first lesson in next module
        next_module = Module.query.filter(
            Module.course_id == module.course_id,
            Module.order_index > module.order_index
        ).order_by(Module.order_index.asc()).first()
        
        if next_module:
            first_lesson_next_module = Lesson.query.filter(
                Lesson.module_id == next_module.id
            ).order_by(Lesson.order_index.asc()).first()
            if first_lesson_next_module:
                next_lesson_id = first_lesson_next_module.id
    
    return jsonify({
        "id": lesson.id,
        "title": lesson.title,
        "video_url": lesson.video_url,
        "duration": lesson.duration,
        "module_title": module.title,
        "course_id": module.course_id,
        "next_lesson_id": next_lesson_id
    })

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

@app.route('/api/generate', methods=['POST'])
def generate_course_api():
    """
    Generate an AI course for a given topic.
    
    Request body: { "topic": "Rust Programming" }
    Response: { "course_id": "rust_programming", "message": "Course generated!" }
    """
    try:
        # Validate request has JSON body
        try:
            data = request.json
        except Exception:
            return jsonify({"error": "Invalid JSON in request body"}), 400
            
        if not data or 'topic' not in data:
            return jsonify({"error": "Missing 'topic' in request body"}), 400
        
        topic = data['topic'].strip()
        if not topic:
            return jsonify({"error": "Topic cannot be empty"}), 400
        
        if len(topic) > 100:
            return jsonify({"error": "Topic too long (max 100 characters)"}), 400
        
        logger.info(f"🎓 Generating course for topic: {topic}")
        
        # Import and call the generator (with fallback for Vercel)
        try:
            from generator import generate_course
        except ImportError:
            from .generator import generate_course
            
        course_id = generate_course(topic, db, Course, Module, Lesson)
        
        return jsonify({
            "course_id": course_id,
            "message": "Course generated successfully!"
        })
        
    except ValueError as e:
        # Handle validation errors (from generator)
        logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        # Catch ALL other errors and return JSON
        error_str = str(e)
        logger.error(f"Course generation failed: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        # Rollback database on any error
        try:
            db.session.rollback()
        except Exception:
            pass
        
        # Handle rate limit (429) or model not found (404) errors
        if "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower():
            return jsonify({
                "error": "AI is busy or cooling down. Please wait 30 seconds and try again.",
                "trace": traceback.format_exc()
            }), 503
        elif "404" in error_str or "not found" in error_str.lower():
            return jsonify({
                "error": "AI is busy or cooling down. Please wait 30 seconds and try again.",
                "trace": traceback.format_exc()
            }), 503
        
        # Return error with full traceback for debugging
        return jsonify({
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500


def _seed_python_course():
    """Helper function to seed Python Mastery course data"""
    # Create Python Mastery course
    python_course = Course(
        id="python",
        title="Python Mastery",
        description="Master Python from scratch to advanced concepts.",
        thumbnail_url="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg",
        level="Beginner",
        is_generated=False
    )
    db.session.add(python_course)
    db.session.flush()
    
    # Module 1: Basics
    module_basics = Module(
        course_id="python",
        title="Basics",
        order_index=1
    )
    db.session.add(module_basics)
    db.session.flush()
    
    basics_lessons = [
        {"title": "Variables & Data Types", "video_id": "_uQrJ0TkZlc", "duration": "10:00"},
        {"title": "Control Flow (If/Else)", "video_id": "Zp5MuPOtsSY", "duration": "12:30"},
        {"title": "Loops (For/While)", "video_id": "6iF8Xb7Z3wQ", "duration": "15:00"}
    ]
    
    for i, lesson_data in enumerate(basics_lessons):
        lesson = Lesson(
            module_id=module_basics.id,
            title=lesson_data["title"],
            video_url=lesson_data["video_id"],
            duration=lesson_data["duration"],
            order_index=i + 1
        )
        db.session.add(lesson)
    
    # Module 2: Data Structures
    module_ds = Module(
        course_id="python",
        title="Data Structures",
        order_index=2
    )
    db.session.add(module_ds)
    db.session.flush()
    
    ds_lessons = [
        {"title": "Lists & Tuples", "video_id": "ohCDkTuyIPg", "duration": "14:20"},
        {"title": "Dictionaries & Sets", "video_id": "daefaLgNkw0", "duration": "11:45"}
    ]
    
    for i, lesson_data in enumerate(ds_lessons):
        lesson = Lesson(
            module_id=module_ds.id,
            title=lesson_data["title"],
            video_url=lesson_data["video_id"],
            duration=lesson_data["duration"],
            order_index=i + 1
        )
        db.session.add(lesson)
    
    # Module 3: OOP
    module_oop = Module(
        course_id="python",
        title="OOP",
        order_index=3
    )
    db.session.add(module_oop)
    db.session.flush()
    
    oop_lessons = [
        {"title": "Classes & Objects", "video_id": "ZDa-Z5JzLYM", "duration": "18:00"},
        {"title": "Inheritance & Polymorphism", "video_id": "JeznW_7DlB0", "duration": "16:10"}
    ]
    
    for i, lesson_data in enumerate(oop_lessons):
        lesson = Lesson(
            module_id=module_oop.id,
            title=lesson_data["title"],
            video_url=lesson_data["video_id"],
            duration=lesson_data["duration"],
            order_index=i + 1
        )
        db.session.add(lesson)
    
    db.session.commit()

@app.route('/api/reset_db', methods=['GET'])
def reset_database():
    """
    WARNING: This route drops ALL tables and recreates them.
    All users will be deleted and must log in again.
    Use this to fix schema sync issues (e.g., missing 'level' column).
    """
    try:
        logger.warning("⚠️ Resetting database - all data will be deleted!")
        
        # Drop all tables
        db.drop_all()
        
        # Recreate tables with updated schema
        db.create_all()
        
        # Seed with Python Mastery course
        _seed_python_course()
        
        logger.info("✅ Database reset and seeded successfully")
        return jsonify({
            "message": "Database reset and seeded successfully. Please Log In again.",
            "warning": "All user data has been deleted."
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database reset failed: {e}")
        return jsonify({"error": f"Reset failed: {str(e)}"}), 500

@app.route('/api/seed_db', methods=['GET'])
def seed_database():
    """Seed the database with Python Mastery course if it doesn't exist"""
    try:
        # Check if Python Mastery course exists
        existing_course = Course.query.filter_by(title="Python Mastery").first()
        
        if existing_course:
            return jsonify({"message": "Database already seeded. Python Mastery course exists."})
        
        _seed_python_course()
        return jsonify({"message": "Database seeded successfully!"})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Seeding failed: {e}")
        return jsonify({"error": f"Seeding failed: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(port=3000, debug=True)