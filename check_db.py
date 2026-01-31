import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("POSTGRES_URL"))
cur = conn.cursor()

cur.execute('SELECT title, description FROM "Course";')
courses = cur.fetchall()

print(f"\n✅ Found {len(courses)} courses in DB:")
for c in courses:
    print(f" - {c[0]}")

conn.close()