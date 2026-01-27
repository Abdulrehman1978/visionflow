from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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