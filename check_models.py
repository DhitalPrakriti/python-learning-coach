from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No API key found in .env")
    raise SystemExit(1)

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(api_version="v1beta"),
)

candidates = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

print(f"STARTING MODEL SCAN... (Key: ...{api_key[-4:]})")
print("-" * 50)

for model in candidates:
    try:
        print(f"Testing: {model.ljust(20)}", end=" ")
        response = client.models.generate_content(model=model, contents="Ping")
        print("SUCCESS" if response.text else "NO TEXT")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print("NOT FOUND (404)")
        elif "401" in error_msg:
            print("AUTH ERROR (401)")
        else:
            print(f"ERROR: {error_msg[:80]}...")

print("-" * 50)
