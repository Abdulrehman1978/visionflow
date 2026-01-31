import os
import json
import time
import requests
import re
from dotenv import load_dotenv
import psycopg2
from rich.console import Console
from rich import print as rprint

# 1. LOAD SECRETS FIRST
load_dotenv()
console = Console()

class DirectCourseFactory:
    """A robust factory using Groq (Fast & Free) to generate courses."""

    def __init__(self):
        # 2. Get Key from Environment (Safely)
        self.api_key = os.getenv("GROQ_API_KEY")
        
        # Fallback: Check if user hardcoded it (for testing)
        if not self.api_key or "gsk" not in self.api_key:
             # Try getting Gemini if Groq is missing
             self.api_key = os.getenv("GEMINI_API_KEY")
             if not self.api_key:
                rprint("[bold red]❌ Error: API Key not found![/bold red]")
                rprint("Make sure your .env file has GROQ_API_KEY='gsk_...'")
                exit(1)
            
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # 3. Database
        self.postgres_url = os.getenv("POSTGRES_URL")
        if not self.postgres_url:
            rprint("[bold red]❌ Error: POSTGRES_URL is missing from .env[/bold red]")
            exit(1)

    def call_ai(self, prompt):
        """Calls Groq's Llama 3.3 model."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Model Name
        data = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"} 
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                rprint(f"[bold red]API Error {response.status_code}: {response.text}[/bold red]")
                return None
        except Exception as e:
            rprint(f"[red]Connection Failed: {e}[/red]")
            return None

    def search_youtube(self, query, limit=3):
        """Simple YouTube scraper."""
        try:
            query_clean = query.replace(' ', '+')
            url = f"https://www.youtube.com/results?search_query={query_clean}"
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            
            seen = set()
            unique_ids = [x for x in video_ids if not (x in seen or seen.add(x))][:limit]
            
            results = []
            for vid in unique_ids:
                results.append({
                    'link': f"https://www.youtube.com/watch?v={vid}",
                    'thumbnail': f"https://img.youtube.com/vi/{vid}/mqdefault.jpg",
                    'duration': "10:00"
                })
            return results
        except Exception as e:
            rprint(f"[yellow]⚠ YouTube Search failed: {e}[/yellow]")
            return []

    def generate_roadmap(self, topic):
        rprint(f"[cyan]🧠 Asking AI to design '{topic}' course...[/cyan]")
        prompt = f"""
        Act as an expert instructor. Create a JSON course roadmap for '{topic}'.
        Strict JSON format.
        Structure:
        {{
            "title": "{topic} Mastery",
            "description": "Complete guide from beginner to expert.",
            "levels": [
                {{
                    "level_name": "Beginner",
                    "topics": [
                        {{ "title": "Topic Name", "subtopics": ["Subtopic 1", "Subtopic 2"] }}
                    ]
                }}
            ]
        }}
        """
        json_text = self.call_ai(prompt)
        if not json_text: return None
        
        try:
            return json.loads(json_text)
        except:
            rprint("[red]❌ AI returned bad JSON. Try again.[/red]")
            return None

    def upload_to_db(self, course_data):
        rprint("[cyan]💾 Connecting to Database...[/cyan]")
        try:
            conn = psycopg2.connect(self.postgres_url)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO "Course" (id, title, description, "thumbnailUrl", "createdAt", "updatedAt")
                VALUES (gen_random_uuid(), %s, %s, %s, NOW(), NOW())
                RETURNING id;
            """, (course_data['title'], course_data['description'], "https://placehold.co/600x400/png"))
            course_id = cur.fetchone()[0]
            
            total_lessons = 0
            for level in course_data['levels']:
                rprint(f"  📂 Level: {level['level_name']}")
                for topic in level['topics']:
                    cur.execute("""
                        INSERT INTO "Module" (id, "courseId", title, "createdAt", "updatedAt")
                        VALUES (gen_random_uuid(), %s, %s, NOW(), NOW())
                        RETURNING id;
                    """, (course_id, topic['title']))
                    module_id = cur.fetchone()[0]
                    
                    for subtopic in topic['subtopics']:
                        time.sleep(1) 
                        videos = self.search_youtube(f"{subtopic} {course_data['title']} tutorial", limit=1)
                        if videos:
                            v = videos[0]
                            cur.execute("""
                                INSERT INTO "Lesson" (id, "moduleId", title, "videoUrl", duration, "thumbnailUrl", "createdAt", "updatedAt")
                                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, NOW(), NOW());
                            """, (module_id, subtopic, v['link'], v['duration'], v['thumbnail']))
                            total_lessons += 1
                        rprint(f"    - Added lesson: {subtopic}")

            conn.commit()
            conn.close()
            rprint(f"\n[bold green]✅ SUCCESS! Created course with {total_lessons} lessons.[/bold green]")
            
        except Exception as e:
            rprint(f"[bold red]❌ Database Error: {e}[/bold red]")

if __name__ == "__main__":
    factory = DirectCourseFactory()
    topic = input("\nEnter course topic: ").strip()
    if topic:
        roadmap = factory.generate_roadmap(topic)
        if roadmap:
            factory.upload_to_db(roadmap)