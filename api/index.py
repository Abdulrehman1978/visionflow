from flask import Flask, jsonify, redirect, url_for, session
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Optional: Load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 1. Init App
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app, supports_credentials=True)

# 2. Database Config (Safe Mode)
database_url = os.getenv("DATABASE_URL")
if not database_url:
    database_url = "sqlite:///visionflow.db"
elif database_url.startswith("postgres://"):
    # Vercel uses postgres:// but SQLAlchemy needs postgresql://
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120))
    avatar = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Course(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    thumbnail_url = db.Column(db.String(200), nullable=True)
    level = db.Column(db.String(50), nullable=True)
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
    video_url = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.String(50), nullable=True)
    order_index = db.Column(db.Integer, nullable=False)

# Initialize DB
with app.app_context():
    db.create_all()

# 4. Auth Setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 5. OAuth Config (Hardcoded for stability)
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

# 6. Routes
@app.route('/')
def home():
    return jsonify({
        "status": "Backend is Online",
        "authenticated": current_user.is_authenticated,
        "user": current_user.email if current_user.is_authenticated else None
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "service": "visionflow-api"})

@app.route('/api/auth/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/callback')
def authorize():
    try:
        token = google.authorize_access_token()
        user_info = google.get('userinfo').json()
        
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
        return redirect(os.getenv("FRONTEND_URL", "http://localhost:5173/dashboard"))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/auth/logout')
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

@app.route('/api/courses', methods=['GET'])
def get_courses():
    courses = Course.query.all()
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
    
    modules = sorted(course.modules, key=lambda x: x.order_index)
    for module in modules:
        lessons = sorted(module.lessons, key=lambda x: x.order_index)
        syllabus["modules"].append({
            "title": module.title,
            "topics": [{
                "id": l.id,
                "name": l.title,
                "video_id": l.video_url,
                "duration": l.duration
            } for l in lessons]
        })
    
    return jsonify(syllabus)

if __name__ == '__main__':
    app.run(port=3000, debug=True)