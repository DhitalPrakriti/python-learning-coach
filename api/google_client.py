# api/google_client.py - small direct Gemini helper
import os

from dotenv import load_dotenv
from google import genai

from agents.base_agent import resolve_model_id

def get_gemini_client():
    """Create a Gemini client using the same environment options as the app.

    Vertex is checked before the API key, matching the coordinator, so a stale
    GEMINI_API_KEY in a developer's .env cannot silently override a deployment.
    """
    load_dotenv()
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true", "yes")

    if use_vertex:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION")
        if not project or not location:
            raise RuntimeError(
                "GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are required for Vertex AI."
            )
        return genai.Client(vertexai=True, project=project, location=location)

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    raise RuntimeError("Set GEMINI_API_KEY or Vertex AI environment variables.")


def generate_content(prompt, **kwargs):
    """Helper for simple one-shot content generation."""
    client = get_gemini_client()
    model = kwargs.pop("model", None) or resolve_model_id()
    response = client.models.generate_content(model=model, contents=prompt, **kwargs)
    return response.text
