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

    def call_ai(self, prompt, use_json_mode=True):
        """Calls Groq's Llama 3.3 model."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Model Name
        data = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if use_json_mode:
            data["response_format"] = {"type": "json_object"}
        
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

    def generate_quizzes(self, video_title):
        """Generates 5 quizzes based on video title using Groq LLM."""
        rprint(f"[yellow]  🧠 Generating Quizzes for {video_title}...[/yellow]")
        
        prompt = f"""
Generate a JSON array of 5 multiple-choice questions based on the topic: "{video_title}".
Each object must have: question, options (array of 4 strings), and correct_answer.

Example format:
{{
    "quizzes": [
        {{
            "question": "What is Python?",
            "options": ["A snake", "A programming language", "A framework", "A library"],
            "correct_answer": "A programming language"
        }}
    ]
}}

Return ONLY valid JSON.
        """
        
        json_text = self.call_ai(prompt, use_json_mode=True)
        if not json_text:
            rprint("[red]  ❌ Quiz generation failed[/red]")
            return []
        
        try:
            data = json.loads(json_text)
            quizzes = data.get('quizzes', [])
            if len(quizzes) < 5:
                rprint(f"[yellow]  ⚠ Only generated {len(quizzes)} quizzes[/yellow]")
            return quizzes[:5]  # Ensure max 5
        except Exception as e:
            rprint(f"[red]  ❌ Failed to parse quiz JSON: {e}[/red]")
            return []

    def course_exists(self, course_title, cursor):
        """Check if a course already exists in the database."""
        cursor.execute('SELECT id FROM "Course" WHERE title = %s', (course_title,))
        return cursor.fetchone() is not None

    def upload_to_db(self, course_data):
        rprint("[cyan]💾 Connecting to Database...[/cyan]")
        try:
            conn = psycopg2.connect(self.postgres_url)
            cur = conn.cursor()
            
            # Check if course already exists
            if self.course_exists(course_data['title'], cur):
                rprint(f"[yellow]⚠ Course '{course_data['title']}' already exists. Skipping...[/yellow]")
                conn.close()
                return
            
            cur.execute("""
                INSERT INTO "Course" (id, title, description, "thumbnailUrl", "createdAt", "updatedAt")
                VALUES (gen_random_uuid(), %s, %s, %s, NOW(), NOW())
                RETURNING id;
            """, (course_data['title'], course_data['description'], "https://placehold.co/600x400/png"))
            course_id = cur.fetchone()[0]
            
            total_lessons = 0
            total_quizzes = 0
            
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
                                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, NOW(), NOW())
                                RETURNING id;
                            """, (module_id, subtopic, v['link'], v['duration'], v['thumbnail']))
                            lesson_id = cur.fetchone()[0]
                            total_lessons += 1
                            
                            # Generate and insert quizzes for this lesson
                            quizzes = self.generate_quizzes(subtopic)
                            for quiz in quizzes:
                                try:
                                    cur.execute("""
                                        INSERT INTO "Quiz" ("lessonId", question, options, "correctAnswer", "createdAt", "updatedAt")
                                        VALUES (%s, %s, %s, %s, NOW(), NOW());
                                    """, (lesson_id, quiz['question'], json.dumps(quiz['options']), quiz['correct_answer']))
                                    total_quizzes += 1
                                except Exception as e:
                                    rprint(f"[red]    ⚠ Failed to insert quiz: {e}[/red]")
                            
                        rprint(f"    - Added lesson: {subtopic}")

            conn.commit()
            conn.close()
            rprint(f"\n[bold green]✅ SUCCESS! Created course with {total_lessons} lessons and {total_quizzes} quizzes.[/bold green]")
            
        except Exception as e:
            rprint(f"[bold red]❌ Database Error: {e}[/bold red]")

if __name__ == "__main__":
    factory = DirectCourseFactory()
    
    # List of all courses to generate
    courses = [
        "Python", 
        "Machine Learning", 
        "Data Science", 
        "HTML", 
        "CSS", 
        "Javascript", 
        "React", 
        "Node.js", 
        "MERN Stack", 
        "Python Libraries"
    ]
    
    rprint(f"[bold cyan]🚀 Starting Course Library Generation ({len(courses)} courses)...[/bold cyan]\n")
    
    for idx, topic in enumerate(courses, 1):
        rprint(f"\n[bold magenta]{'='*60}[/bold magenta]")
        rprint(f"[bold magenta]Course {idx}/{len(courses)}: {topic}[/bold magenta]")
        rprint(f"[bold magenta]{'='*60}[/bold magenta]\n")
        
        roadmap = factory.generate_roadmap(topic)
        if roadmap:
            factory.upload_to_db(roadmap)
        else:
            rprint(f"[red]❌ Failed to generate roadmap for {topic}[/red]")
        
        # Small delay between courses to avoid rate limiting
        if idx < len(courses):
            time.sleep(2)
    
    rprint(f"\n[bold green]🎉 Course Library Generation Complete![/bold green]")