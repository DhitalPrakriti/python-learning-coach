# api/google_client.py - KEEP AS FALLBACK/UTILITY
from vertexai.generative_models import GenerativeModel
from config.settings import MODEL_NAME

def get_gemini_client():
    """Get configured Gemini client using Vertex AI - for simple tasks"""
    return GenerativeModel(MODEL_NAME)

def generate_content(prompt, **kwargs):
    """Helper function for simple content generation"""
    model = get_gemini_client()
    response = model.generate_content(prompt, **kwargs)
    return response.text

print("✅ Vertex AI client configured for simple tasks")