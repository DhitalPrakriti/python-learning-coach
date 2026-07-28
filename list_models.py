from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No API key found in .env")
    raise SystemExit(1)

print(f"Using key: ...{api_key[-5:]}")

try:
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(api_version="v1beta"),
    )

    print("Connecting to Google AI Studio...")
    all_models = client.models.list()

    print("\nCONNECTION SUCCESSFUL. Available Gemini models:")
    print("=" * 60)

    found_gemini = False
    for model in all_models:
        if "gemini" in model.name:
            clean_name = model.name.split("/")[-1]
            print(f"- {clean_name}")
            found_gemini = True

    if not found_gemini:
        print("WARNING: Connected, but no models with 'gemini' in the name were returned.")

    print("=" * 60)

except Exception as e:
    print(f"\nCONNECTION FAILED: {str(e)}")
    print("\nTroubleshooting:")
    if "401" in str(e):
        print("-> Your API key is invalid or this library is still trying to hit Vertex AI.")
    elif "404" in str(e):
        print("-> The API endpoint was not found. Check api_version.")
