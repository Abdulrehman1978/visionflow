import os
import json
import time
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from youtubesearchpython import VideosSearch
import psycopg2
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

# --- FIX: MONKEY PATCH FOR YOUTUBE PROXIES BUG ---
# This forces the requests library to ignore the 'proxies' argument that causes the crash
original_post = requests.post
def patched_post(*args, **kwargs):
    kwargs.pop('proxies', None)
    return original_post(*args, **kwargs)
requests.post = patched_post
# ---------------------------------------------------

load_dotenv()
console = Console()

class CourseGenerator:
    """Generates structured courses with validated video content."""

    def __init__(self, api_key: str):
        """Initialize with auto-fallback for model names."""
        if not api_key:
            rprint("[bold red]❌ Error: GEMINI_API_KEY is missing from .env[/bold red]")
            exit(1)
            
        genai.configure(api_key=api_key)
        
        # Try Flash first (Fast), fallback to Pro (Stable)
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            # Test connection
            self.model.generate_content("test")
            self.model_name = "Gemini 1.5 Flash"
        except Exception:
            try:
                self.model = genai.GenerativeModel('gemini-pro')
                self.model_name = "Gemini Pro"
            except Exception as e:
                rprint(f"[bold red]❌ Critical Error: Could not connect to any Gemini model.[/bold red]")
                rprint(f"Details: {e}")
                exit(1)

        rprint(f"[green]✔ Connected to AI Model: {self.model_name}[/green]")

    def generate_roadmap(self, topic: str):
        """Generates the course syllabus."""
        system_prompt = f"""
        Act as an expert instructor. Create a complete, structured course roadmap for learning '{topic}'.
        
        Strict Output Format (JSON ONLY):
        {{
            "title": "{topic} Mastery",
            "description": "A complete guide from beginner to expert.",
            "levels": [
                {{
                    "level_name": "Beginner",
                    "topics": [
                        {{ "title": "Topic Name", "subtopics": ["Subtopic 1", "Subtopic 2"] }}
                    ]
                }}
            ]
        }}
        Do NOT use Markdown formatting (no ```json). Just raw JSON.
        """
        
        try:
            response = self.model.generate_content(system_prompt)
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            rprint(f"[red]Error generating roadmap: {e}[/red]")
            return None

    def get_keywords(self, subtopic: str):
        """Extracts validation keywords."""
        prompt = f"""
        Act as a syllabus analyst. Convert the topic '{subtopic}' into 5-10 single-word learning indicators.
        Output ONLY comma-separated words. No explanation.
        Example: "Variables" -> variable, storage, value, declare, assign, type
        """
        try:
            response = self.model.generate_content(prompt)
            return [w.strip() for w in response.text.split(',')]
        except:
            return []

    def find_videos(self, query: str, limit=3):
        """Finds videos using the fixed library."""
        try:
            search = VideosSearch(query, limit=limit)
            return search.result().get('result', [])
        except Exception as e:
            rprint(f"[yellow]⚠ Video search warning: {e}[/yellow]")
            return []

    def find_crash_courses(self, topic: str):
        """Finds long-form courses."""
        rprint(f"\n🎬 [bold]Finding One-Shot Crash Courses for {topic}...[/bold]")
        query = f"{topic} full course"
        try:
            results = self.find_videos(query, limit=5)
            # Simple filter for long videos (naive check for 'hour' in duration text)
            crash_courses = [v for v in results if 'hour' in v.get('duration', '').lower() or 'hr' in v.get('duration', '').lower()]
            
            if crash_courses:
                rprint(f"[green]✔ Found {len(crash_courses)} Crash Courses[/green]")
            else:
                rprint("[yellow]No crash courses found (might be short videos only).[/yellow]")
                
            return crash_courses
        except Exception as e:
            rprint(f"[red]Error finding crash courses: {e}[/red]")
            return []

    def upload_to_db(self, course_data, crash_courses):
        """Uploads the generated data to Postgres."""
        conn_string = os.getenv("POSTGRES_URL")
        if not conn_string:
            rprint("[red]❌ Error: POSTGRES_URL missing from .env[/red]")
            return

        try:
            conn = psycopg2.connect(conn_string)
            cur = conn.cursor()
            
            # 1. Create Course
            rprint("[cyan]Uploading Course Header...[/cyan]")
            cur.execute("""
                INSERT INTO "Course" (id, title, description, "thumbnailUrl", "createdAt", "updatedAt")
                VALUES (gen_random_uuid(), %s, %s, %s, NOW(), NOW())
                RETURNING id;
            """, (course_data['title'], course_data['description'], "[https://placehold.co/600x400/png](https://placehold.co/600x400/png)"))
            course_id = cur.fetchone()[0]

            # 2. Upload Crash Courses (as separate Modules or References if you prefer)
            # For now, we will print them. (You can add logic to save them to a 'Resource' table later)
            
            # 3. Upload Syllabus
            total_topics = 0
            for level in course_data['levels']:
                rprint(f"  📂 Processing Level: {level['level_name']}")
                for topic in level['topics']:
                    # Create Module
                    cur.execute("""
                        INSERT INTO "Module" (id, "courseId", title, "createdAt", "updatedAt")
                        VALUES (gen_random_uuid(), %s, %s, NOW(), NOW())
                        RETURNING id;
                    """, (course_id, topic['title']))
                    module_id = cur.fetchone()[0]

                    # Create Lessons (Subtopics)
                    for subtopic in topic['subtopics']:
                        # Find Video
                        videos = self.find_videos(f"{subtopic} tutorial", limit=1)
                        video_url = videos[0]['link'] if videos else "[https://youtube.com](https://youtube.com)"
                        duration = videos[0]['duration'] if videos else "10:00"
                        thumb = videos[0]['thumbnails'][0]['url'] if videos else ""

                        cur.execute("""
                            INSERT INTO "Lesson" (id, "moduleId", title, "videoUrl", duration, "thumbnailUrl", "createdAt", "updatedAt")
                            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, NOW(), NOW());
                        """, (module_id, subtopic, video_url, duration, thumb))
                        total_topics += 1
                        
            conn.commit()
            cur.close()
            conn.close()
            rprint(f"[bold green]✅ Success! Uploaded {total_topics} lessons to DB.[/bold green]")
            
        except Exception as e:
            rprint(f"[bold red]❌ Database Error: {e}[/bold red]")

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    generator = CourseGenerator(api_key)

    topic = input("\nEnter course topic (e.g., Python, JavaScript): ").strip()
    if not topic:
        return

    # 1. Find Crash Courses
    crash_courses = generator.find_crash_courses(topic)

    # 2. Generate Roadmap
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task(f"[cyan]Generating Roadmap for {topic}...", total=None)
        roadmap = generator.generate_roadmap(topic)
        
    if roadmap:
        rprint("\n[bold]🗺️  Roadmap Generated![/bold]")
        # 3. Upload
        generator.upload_to_db(roadmap, crash_courses)

if __name__ == "__main__":
    main()