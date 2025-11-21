from google.adk.models.google_llm import Gemini
from google.genai import types
from config.settings import GOOGLE_API_KEY, MODEL_NAME

def get_gemini_client():
    """Get configured Gemini client for all agents"""
    return Gemini(model_name=MODEL_NAME, api_key=GOOGLE_API_KEY)

def get_retry_config():
    """Get HTTP retry configuration"""
    return types.HttpRetryOptions(
        attempts=5,
        exp_base=7, 
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )
