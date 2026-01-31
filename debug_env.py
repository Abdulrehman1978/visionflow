import os
from dotenv import load_dotenv

# Force it to look in the current directory
current_dir = os.getcwd()
env_path = os.path.join(current_dir, '.env')

print(f"1. Looking for .env at: {env_path}")
print(f"2. Does file exist? {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("3. File content preview:")
    with open(env_path, 'r') as f:
        print(f.read())
else:
    print("   ERROR: File not found!")

print("-" * 20)
load_dotenv()
print(f"4. GEMINI_API_KEY value: {os.getenv('GEMINI_API_KEY')}")    