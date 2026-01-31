import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Get the URL from .env
db_url = os.getenv("POSTGRES_URL")

if not db_url:
    print("❌ Error: POSTGRES_URL not found in .env")
    exit(1)

print("🔌 Connecting to database...")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # 1. Create Course Table
    print("🔨 Creating 'Course' table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Course" (
            "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            "title" TEXT NOT NULL,
            "description" TEXT,
            "thumbnailUrl" TEXT,
            "createdAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Create Module Table
    print("🔨 Creating 'Module' table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Module" (
            "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            "courseId" UUID NOT NULL REFERENCES "Course"("id") ON DELETE CASCADE,
            "title" TEXT NOT NULL,
            "createdAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Create Lesson Table
    print("🔨 Creating 'Lesson' table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Lesson" (
            "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            "moduleId" UUID NOT NULL REFERENCES "Module"("id") ON DELETE CASCADE,
            "title" TEXT NOT NULL,
            "videoUrl" TEXT,
            "duration" TEXT,
            "thumbnailUrl" TEXT,
            "createdAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("\n✅ Success! Database tables created. You can now run the course factory.")

except Exception as e:
    print(f"\n❌ Error creating tables: {e}")