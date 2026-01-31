import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("POSTGRES_URL"))
cur = conn.cursor()

# Check if Quiz table exists and get its schema
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'quiz'
    ORDER BY ordinal_position;
""")

columns = cur.fetchall()
if columns:
    print("\n✅ Quiz table schema:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")
else:
    print("\n❌ Quiz table does not exist yet")
    print("It will be created by SQLAlchemy when the Flask app runs")

conn.close()
