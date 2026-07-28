import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

# Runtime mode
LOCAL_ONLY = os.getenv("LOCAL_ONLY", "").lower() in ("1", "true", "yes")
FIRESTORE_ENABLED = os.getenv("FIRESTORE_ENABLED", "").lower() in ("1", "true", "yes")

# Gemini / Vertex AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# os.getenv's default is evaluated eagerly, so an empty ADK_MODEL="" would win
# over GEMINI_MODEL. `or` chaining treats empty the same as unset.
GEMINI_MODEL = os.getenv("ADK_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in (
    "1",
    "true",
    "yes",
)
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "northamerica-northeast1")

# Flask
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# Learning coach defaults
DEFAULT_SUBJECT = "python"
DEFAULT_USER_ID = "default_user"
DEFAULT_LEVEL = "beginner"
DEFAULT_LEARNING_STYLE = "adaptive"
SUPPORTED_LEVELS = ["beginner", "intermediate", "advanced"]
LEARNING_STYLES = ["visual", "auditory", "kinesthetic", "adaptive"]
MAX_CONVERSATION_HISTORY = 50

# Request limits. A learner question does not need more than this, and the cap
# keeps a single oversized paste from consuming the API budget.
MAX_MESSAGE_CHARS = int(os.getenv("MAX_MESSAGE_CHARS", 4000))
MAX_USER_ID_CHARS = 64

CORE_PYTHON_TOPICS = [
    "variables",
    "data_types",
    "operators",
    "conditionals",
    "loops",
    "functions",
    "lists",
    "dictionaries",
    "tuples",
    "sets",
    "classes",
    "inheritance",
    "modules",
    "file_handling",
    "error_handling",
]

AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "assessment": {"description": "Python skill assessor"},
    "curriculum": {"description": "Personalized learning path designer"},
    "teaching": {"description": "Patient Python tutor"},
    "practice": {"description": "Coding exercise creator"},
    "progress": {"description": "Learning progress tracker"},
}


def runtime_mode() -> str:
    if LOCAL_ONLY:
        return "local"
    if GEMINI_API_KEY:
        return "gemini_api_key"
    if GOOGLE_GENAI_USE_VERTEXAI:
        return "vertex_ai"
    return "local"
