# config/settings.py - ENHANCED VERSION
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

# ============ VERTEX AI CONFIGURATION ============
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "python-learning-coach-ai")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# Validate required environment variables
REQUIRED_ENV_VARS = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS"]
for var in REQUIRED_ENV_VARS:
    if not os.environ.get(var) and var != "GOOGLE_APPLICATION_CREDENTIALS":  # Creds can be implicit
        print(f"⚠️  Warning: {var} not set. Using default/local authentication.")

# ============ MODEL CONFIGURATION ============
# ADK compatible models (check Google's latest documentation)
SUPPORTED_ADK_MODELS = [
    "gemini-1.5-flash-001",
    "gemini-1.5-pro-001", 
    "gemini-1.0-pro"
]

ADK_MODEL_NAME = os.environ.get("ADK_MODEL", "gemini-1.5-flash-001")
if ADK_MODEL_NAME not in SUPPORTED_ADK_MODELS:
    print(f"⚠️  Warning: {ADK_MODEL_NAME} may not be fully compatible with ADK")

# For direct Gemini fallback (optional)
FALLBACK_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-001")

# ============ ADK AGENT CONFIGURATION ============
# Base configuration for all agents
BASE_AGENT_CONFIG = {
    "model": ADK_MODEL_NAME,
    "temperature": 0.3,
    "top_p": 0.8,
    "max_output_tokens": 1024,
}

# Agent-specific overrides
ADK_AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "assessment": {
        "name": "assessment_agent",
        "temperature": 0.2,  # More deterministic for assessments
        "max_output_tokens": 1024,
        "description": "Python skill assessor that evaluates programming proficiency"
    },
    "curriculum": {
        "name": "curriculum_agent", 
        "temperature": 0.4,  # More creative for curriculum design
        "max_output_tokens": 2048,
        "description": "Personalized learning path designer for Python"
    },
    "teaching": {
        "name": "teaching_agent",
        "temperature": 0.3,  # Balanced for explanations
        "max_output_tokens": 1536,
        "description": "Patient Python tutor explaining concepts clearly"
    },
    "practice": {
        "name": "practice_agent",
        "temperature": 0.3,  # Consistent for exercise generation
        "max_output_tokens": 1280,
        "description": "Coding exercise creator for hands-on practice"
    },
    "progress": {
        "name": "progress_agent",
        "temperature": 0.2,  # More factual for progress tracking
        "max_output_tokens": 1024,
        "description": "Learning progress tracker and motivational coach"
    }
}

# Merge base config with agent-specific configs
for agent_name, config in ADK_AGENT_CONFIGS.items():
    ADK_AGENT_CONFIGS[agent_name] = {**BASE_AGENT_CONFIG, **config}

# ============ LEARNING COACH SETTINGS ============
DEFAULT_SUBJECT = "python"
DEFAULT_USER_ID = "default_user"
DEFAULT_LEVEL = "beginner"
DEFAULT_LEARNING_STYLE = "adaptive"

SUPPORTED_LEVELS = ["beginner", "intermediate", "advanced"]
LEARNING_STYLES = ["visual", "auditory", "kinesthetic", "adaptive"]

# Context management
MAX_TOPICS_HISTORY = 50
MAX_CONVERSATION_HISTORY = 20  # Reduced from 100 for performance
MAX_USER_CONTEXTS = 1000  # Prevent memory leaks in production

# Learning paths
CORE_PYTHON_TOPICS = [
    "variables", "data_types", "operators", "conditionals", "loops",
    "functions", "lists", "dictionaries", "tuples", "sets",
    "classes", "inheritance", "modules", "file_handling", "error_handling"
]

# ============ API & DEPLOYMENT SETTINGS ============
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
WORKERS = int(os.environ.get("WORKERS", 4))

# Rate limiting (optional)
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT", 60))

# ============ PATHS ============
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# ============ LOGGING CONFIGURATION ============
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGS_DIR, "learning_coach.log"),
            "formatter": "standard"
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"] if not DEBUG else ["console"],
            "level": LOG_LEVEL,
            "propagate": True
        }
    }
}

# Print configuration summary
if DEBUG:
    print(f"✅ ADK Learning Coach Configuration")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Location: {LOCATION}")
    print(f"   ADK Model: {ADK_MODEL_NAME}")
    print(f"   Fallback Model: {FALLBACK_MODEL}")
    print(f"   Agents: {list(ADK_AGENT_CONFIGS.keys())}")
    print(f"   Debug Mode: {DEBUG}")
    print(f"   Port: {PORT}")