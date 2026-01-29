"""
AI Course Generator Module

Uses Google Gemini to generate course syllabus and YouTube to curate videos.
"""

import os
import json
import logging
import re
from google import genai
from youtubesearchpython import VideosSearch

logger = logging.getLogger(__name__)

def get_gemini_client():
    """Initialize and return Gemini client"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)

def generate_syllabus(topic_name: str) -> dict:
    """
    Use Gemini to generate a structured course syllabus.
    
    Returns a dict with 'title', 'description', 'level', and 'modules'.
    Each module has 'title' and 'lessons' (list of lesson title strings).
    """
    client = get_gemini_client()
    
    prompt = f"""Create a structured online course for learning "{topic_name}".
    
Return ONLY valid JSON (no markdown, no code blocks). The structure must be:
{{
    "title": "Course Title",
    "description": "A concise course description (1-2 sentences)",
    "level": "Beginner" or "Intermediate" or "Advanced",
    "modules": [
        {{
            "title": "Module Title",
            "lessons": ["Lesson 1 title", "Lesson 2 title", "Lesson 3 title"]
        }}
    ]
}}

Requirements:
- Create exactly 3-4 modules
- Each module should have 2-4 lessons
- Lesson titles should be specific and searchable on YouTube
- Module titles should be clear categories
- Make lesson titles descriptive (e.g., "Variables and Data Types in Python" not just "Variables")
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        # Clean the response - remove markdown code blocks if present
        text = response.text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        
        syllabus = json.loads(text)
        
        # Validate required fields
        if not all(key in syllabus for key in ['title', 'modules']):
            raise ValueError("Missing required fields in syllabus")
        
        return syllabus
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Raw response: {response.text[:500]}")
        raise ValueError(f"Gemini returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise

def search_youtube_video(query: str) -> dict:
    """
    Search YouTube for a video matching the query.
    Returns video info dict with 'id', 'title', 'duration'.
    """
    try:
        search = VideosSearch(query + " tutorial", limit=1)
        results = search.result()
        
        if not results or not results.get('result'):
            logger.warning(f"No YouTube results for: {query}")
            return {
                'id': 'dQw4w9WgXcQ',  # Fallback to a known video
                'title': query,
                'duration': '10:00'
            }
        
        video = results['result'][0]
        return {
            'id': video.get('id', ''),
            'title': video.get('title', query),
            'duration': video.get('duration', '10:00')
        }
        
    except Exception as e:
        logger.error(f"YouTube search failed for '{query}': {e}")
        return {
            'id': 'dQw4w9WgXcQ',
            'title': query,
            'duration': '10:00'
        }

def generate_course(topic_name: str, db, Course, Module, Lesson) -> str:
    """
    Main function to generate a complete course.
    
    1. Generate syllabus with Gemini
    2. Find YouTube videos for each lesson
    3. Save to database
    
    Returns the course ID.
    """
    logger.info(f"🚀 Generating course for: {topic_name}")
    
    # Step 1: Generate syllabus
    syllabus = generate_syllabus(topic_name)
    logger.info(f"📚 Syllabus generated: {syllabus['title']}")
    
    # Create a slug ID from the title
    course_id = syllabus['title'].lower().replace(' ', '_').replace('-', '_')
    course_id = re.sub(r'[^a-z0-9_]', '', course_id)[:50]
    
    # Check if course already exists
    existing = Course.query.filter_by(id=course_id).first()
    if existing:
        # Add a random suffix to make it unique
        import random
        course_id = f"{course_id}_{random.randint(100, 999)}"
    
    # Step 2: Create Course
    course = Course(
        id=course_id,
        title=syllabus['title'],
        description=syllabus.get('description', f"Master {topic_name} from scratch"),
        thumbnail_url=f"https://img.youtube.com/vi/placeholder/mqdefault.jpg",
        level=syllabus.get('level', 'Beginner'),
        is_generated=True
    )
    db.session.add(course)
    db.session.flush()
    
    # Step 3: Create Modules and Lessons
    for module_idx, module_data in enumerate(syllabus['modules']):
        module = Module(
            course_id=course_id,
            title=module_data['title'],
            order_index=module_idx + 1
        )
        db.session.add(module)
        db.session.flush()
        
        lessons = module_data.get('lessons', [])
        for lesson_idx, lesson_title in enumerate(lessons):
            # Search for YouTube video
            logger.info(f"  🔍 Searching video for: {lesson_title}")
            video_info = search_youtube_video(lesson_title)
            
            lesson = Lesson(
                module_id=module.id,
                title=lesson_title,
                video_url=video_info['id'],
                duration=video_info['duration'],
                order_index=lesson_idx + 1
            )
            db.session.add(lesson)
            
            # Update thumbnail to first video if not set
            if module_idx == 0 and lesson_idx == 0:
                course.thumbnail_url = f"https://img.youtube.com/vi/{video_info['id']}/mqdefault.jpg"
    
    db.session.commit()
    logger.info(f"✅ Course '{syllabus['title']}' saved with ID: {course_id}")
    
    return course_id
