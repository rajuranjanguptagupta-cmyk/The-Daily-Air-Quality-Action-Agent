"""
Helper script to set the GROQ_API_KEY in the .env file.
Usage:  python set_groq_key.py  gsk_XXXXXXXXXXXXXXXXXXXX
"""
import sys, os, re

key = sys.argv[1].strip() if len(sys.argv) > 1 else ""
if not key:
    print("Usage: python set_groq_key.py  gsk_XXXXXXX")
    sys.exit(1)

env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    print(f".env file not found at {env_path}")
    sys.exit(1)

with open(env_path, "r") as f:
    content = f.read()

if "GROQ_API_KEY=" in content:
    content = re.sub(r"GROQ_API_KEY=.*", f"GROQ_API_KEY={key}", content)
else:
    content += f"\nGROQ_API_KEY={key}\n"

with open(env_path, "w") as f:
    f.write(content)

print(f"[OK] GROQ_API_KEY set in .env")
print("Now run:  python run.py")
